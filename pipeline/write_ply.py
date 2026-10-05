"""Write dec_verts/dec_faces + uv/normals from the Draco decode to a textured binary PLY."""
import numpy as np
import DracoPy, struct, json

# re-decode to get all attributes (npy only saved points/faces)
d = open('data/shingle-roof.glb','rb').read()
clen, ctype = struct.unpack('<II', d[12:20])
js = json.loads(d[20:20+clen])
blen, btype = struct.unpack('<II', d[20+clen:28+clen])
bin0 = 20+clen+8
binbuf = d[bin0:bin0+blen]
bv = js['bufferViews'][1]
blob = binbuf[bv.get('byteOffset',0):bv.get('byteOffset',0)+bv['byteLength']]
mesh = DracoPy.decode(blob)
V = np.asarray(mesh.points, dtype=np.float32)
N = np.asarray(mesh.normals, dtype=np.float32)
UV = np.asarray(mesh.tex_coord, dtype=np.float32)
F = np.asarray(mesh.faces, dtype=np.int32).reshape(-1,3)
print('V', V.shape, 'N', N.shape, 'UV', UV.shape, 'F', F.shape, flush=True)

with open('dec_textured.ply','wb') as f:
    hdr = f"""ply
format binary_little_endian 1.0
element vertex {len(V)}
property float x
property float y
property float z
property float nx
property float ny
property float nz
element face {len(F)}
property list uchar int vertex_indices
property list uchar float texcoord
end_header
"""
    f.write(hdr.encode())
    vn = np.hstack([V, N]).astype('<f4')
    f.write(vn.tobytes())
    # faces: uchar count(3) + 3x int32 + uchar count(6) + 6x float32
    fuv = UV[F]  # (nf,3,2)
    out = bytearray()
    for i in range(len(F)):
        out += b'\x03' + F[i].astype('<i4').tobytes() + b'\x06' + fuv[i].astype('<f4').tobytes()
    f.write(bytes(out))
print('dec_textured.ply written', flush=True)
