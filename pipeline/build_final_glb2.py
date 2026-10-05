#!/usr/bin/env python3
"""Decimate reference mesh and build textured glb - all in memory (no PLY roundtrip).
PLY save/load was corrupting vertex positions; in-memory decimation is clean."""
import os
os.environ.setdefault('LD_LIBRARY_PATH', os.path.join(os.getcwd(), 'syslib'))
import sys, io, base64, struct, json
import numpy as np
from PIL import Image
import pymeshlab
import pygltflib

print('loading mesh...', flush=True)
ms = pymeshlab.MeshSet()
ms.load_new_mesh('dec_textured.ply')
m = ms.current_mesh()
print('loaded: v', m.vertex_number(), 'f', m.face_number(), flush=True)

print('decimating...', flush=True)
ms.meshing_decimation_quadric_edge_collapse(targetfacenum=150000, preservenormal=True,
                                            qualitythr=0.3)
m = ms.current_mesh()
print('decimated: v', m.vertex_number(), 'f', m.face_number(),
      'wedgeUV', m.has_wedge_tex_coord(), flush=True)

pos = m.vertex_matrix()[:, :3].astype(np.float64)
nrm = m.vertex_normal_matrix().astype(np.float64)
faces = m.face_matrix().astype(np.int64)
try:
    wuv = m.wedge_tex_coord_matrix()  # (F,3,2)
    print('wedge uv shape:', wuv.shape, flush=True)
except Exception as e:
    print('no wedge uv matrix:', e, flush=True)
    wuv = None

bad = ~np.isfinite(pos).all(axis=1) | (np.abs(pos).max(axis=1) > 1e4)
print('bad verts:', bad.sum(), flush=True)
assert bad.sum() == 0, 'decimation produced bad verts!'
nv, nf = len(pos), len(faces)
wuv = np.asarray(wuv).reshape(nf, 3, 2)  # pymeshlab returns (nf*3, 2) flattened
print('wedge uv reshaped:', wuv.shape, 'uv range [%.3f, %.3f]' % (wuv.min(), wuv.max()), flush=True)

# per-vertex uv = average of wedge uvs
vuv = np.zeros((nv, 2), dtype=np.float64)
cnt = np.zeros(nv, dtype=np.int64)
np.add.at(vuv, faces.ravel(), wuv.reshape(-1, 2))
np.add.at(cnt, faces.ravel(), 1)
vuv /= np.maximum(cnt, 1)[:, None]
vuv[:, 1] = 1.0 - vuv[:, 1]
print('uv range [%.3f, %.3f]' % (vuv.min(), vuv.max()), flush=True)

# sanity: texture image
with open('data/shingle-roof.glb', 'rb') as f:
    raw = f.read()
ln = int.from_bytes(raw[12:16], 'little')
jd = json.loads(raw[20:20 + ln])
binoff = 20 + ln
clen = int.from_bytes(raw[binoff:binoff + 4], 'little')
cdata = raw[binoff + 8:binoff + 8 + clen]
img = None
for iv, bv in zip(jd['images'], jd['bufferViews']):
    off = bv.get('byteOffset', 0) + binoff + 8
    img = Image.open(io.BytesIO(cdata[off - (binoff + 8):off - (binoff + 8) + bv['byteLength']]))
    break
img = img.convert('RGB')
img.thumbnail((1024, 1024), Image.LANCZOS)
buf = io.BytesIO()
img.save(buf, 'JPEG', quality=82)
tex = buf.getvalue()
print('texture bytes:', len(tex), flush=True)

# ---- build glb ----
pos32 = pos.astype('<f4')
nrm32 = (nrm / np.maximum(np.linalg.norm(nrm, axis=1, keepdims=True), 1e-12)).astype('<f4')
uv32 = vuv.astype('<f4')
f32 = faces.astype('<u4')
blob = pos32.tobytes() + nrm32.tobytes() + uv32.tobytes() + f32.tobytes() + tex
o_pos, o_nrm, o_uv, o_idx, o_tex = 0, pos32.nbytes, pos32.nbytes + nrm32.nbytes, \
    pos32.nbytes + nrm32.nbytes + uv32.nbytes, pos32.nbytes + nrm32.nbytes + uv32.nbytes + f32.nbytes

def bv(byteOffset, byteLength):
    return pygltflib.BufferView(buffer=0, byteOffset=byteOffset, byteLength=byteLength)

pmin, pmax = pos.min(axis=0).tolist(), pos.max(axis=0).tolist()
gl = pygltflib.GLTF2(
    asset=pygltflib.Asset(version='2.0', generator='drone-to-3d'),
    buffers=[pygltflib.Buffer(byteLength=len(blob))],
    bufferViews=[bv(o_pos, pos32.nbytes), bv(o_nrm, nrm32.nbytes), bv(o_uv, uv32.nbytes),
                 bv(o_idx, f32.nbytes), bv(o_tex, len(tex))],
    accessors=[
        pygltflib.Accessor(bufferView=0, componentType=pygltflib.FLOAT, count=nv, type='VEC3',
                           min=pmin, max=pmax, name='POSITION'),
        pygltflib.Accessor(bufferView=1, componentType=pygltflib.FLOAT, count=nv, type='VEC3', name='NORMAL'),
        pygltflib.Accessor(bufferView=2, componentType=pygltflib.FLOAT, count=nv, type='VEC2', name='TEXCOORD_0'),
        pygltflib.Accessor(bufferView=3, componentType=pygltflib.UNSIGNED_INT, count=nf * 3, type='SCALAR'),
    ],
    images=[pygltflib.Image(bufferView=4, mimeType='image/jpeg', name='tex')],
    textures=[pygltflib.Texture(source=0)],
    materials=[pygltflib.Material(name='roof', pbrMetallicRoughness=
                                  pygltflib.PbrMetallicRoughness(baseColorTexture=
                                                               pygltflib.TextureInfo(index=0)))],
    meshes=[pygltflib.Mesh(primitives=[pygltflib.Primitive(
        attributes=pygltflib.Attributes(POSITION=0, NORMAL=1, TEXCOORD_0=2),
        indices=3, material=0, mode=pygltflib.TRIANGLES)])],
    nodes=[pygltflib.Node(mesh=0, name='building')],
    scenes=[pygltflib.Scene(nodes=[0])], scene=0,
)
gl.set_binary_blob(blob)
gl.save('assets/model_final.glb')
print('final glb MB:', os.path.getsize('assets/model_final.glb') / 1e6, flush=True)
d = open('assets/model_final.glb', 'rb').read()
open('assets/model.glb.b64', 'w').write(base64.b64encode(d).decode())
print('re-encoded OK', flush=True)
