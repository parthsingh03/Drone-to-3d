"""Pack assets for the page:
1. sparse_cloud.ply -> decimated binary point buffer (Float32 xyz + Uint8 rgb) -> assets/cloud.bin.b64 + cloud.meta.json
2. data/shingle-roof.glb -> downscaled textures -> assets/model.glb.b64
3. 8 sample photos (640px) -> assets/photo_{i}.b64
4. stats.json
Run with stats updated after reconstruction. Env: venv python."""
import os, json, base64, struct, random
import numpy as np
from PIL import Image

os.makedirs('assets', exist_ok=True)

# ---------- 1. point cloud ----------
def read_ply(path):
    with open(path, 'rb') as f:
        header = b''
        while True:
            line = f.readline()
            header += line
            if line.strip() == b'end_header':
                break
        h = header.decode('ascii', 'ignore')
        n = int([l for l in h.splitlines() if l.startswith('element vertex')][0].split()[-1])
        is_bin = 'format binary_little_endian' in h
        props = [l.split()[-1] for l in h.splitlines() if l.startswith('property')]
        if not is_bin:
            raise RuntimeError('only binary PLY supported')
        # map property -> (dtype, offset)
        dtypes = {'float': ('f', 4), 'float32': ('f', 4), 'uchar': ('B', 1), 'uint8': ('B', 1)}
        fmt, size = '', 0
        for l in h.splitlines():
            if l.startswith('property'):
                _, typ, name = l.split()
                code, sz = dtypes[typ]
                fmt += code
                size += sz
        data = f.read(n * size)
        arr = np.frombuffer(data, dtype=np.dtype({'names': props, 'formats': [c for c in fmt],
                                                  'offsets': np.cumsum([0] + [ {'f':4,'B':1}[c] for c in fmt])[:-1],
                                                  'itemsize': size}))
        xs = arr['x'].astype(np.float32); ys = arr['y'].astype(np.float32); zs = arr['z'].astype(np.float32)
        rs = arr['red'].astype(np.uint8) if 'red' in props else np.zeros(n, np.uint8)
        gs = arr['green'].astype(np.uint8) if 'green' in props else np.zeros(n, np.uint8)
        bs = arr['blue'].astype(np.uint8) if 'blue' in props else np.zeros(n, np.uint8)
        return xs, ys, zs, rs, gs, bs

xs, ys, zs, rs, gs, bs = read_ply('sparse_cloud.ply')
n_all = len(xs)
print('PLY points:', n_all)
MAXP = 60000
idx = np.arange(n_all)
if n_all > MAXP:
    rng = np.random.default_rng(7)
    idx = np.sort(rng.choice(n_all, MAXP, replace=False))
xs, ys, zs, rs, gs, bs = xs[idx], ys[idx], zs[idx], rs[idx], gs[idx], bs[idx]
n = len(xs)
buf = bytearray()
for i in range(n):
    buf += struct.pack('<fff', float(xs[i]), float(ys[i]), float(zs[i]))
    buf += bytes([int(rs[i]), int(gs[i]), int(bs[i])])
with open('assets/cloud.bin.b64', 'w') as f:
    f.write(base64.b64encode(bytes(buf)).decode())
with open('assets/cloud.meta.json', 'w') as f:
    json.dump({'n': n, 'all': n_all}, f)
print(f'cloud packed: {n} pts, b64 {len(buf)*4/3/1e6:.1f} MB')

# ---------- 2. glb texture downscale ----------
from pygltflib import GLTF2
g = GLTF2().load('data/shingle-roof.glb')
print('glb images:', len(g.images or []))
for im_i, im in enumerate(g.images or []):
    bv = g.bufferViews[im.bufferView]
    blob = bytes(g.binary_blob()[bv.byteOffset:bv.byteOffset + bv.byteLength])
    pic = Image.open(__import__('io').BytesIO(blob))
    print(f'  tex {im_i}: {pic.size} {pic.mode}')
    if max(pic.size) > 1024:
        pic.thumbnail((1024, 1024), Image.LANCZOS)
        out = __import__('io').BytesIO()
        pic.convert('RGB').save(out, 'JPEG', quality=82)
        blob = out.getvalue()
    # replace bufferView content (rebuild binary at end for simplicity)
    im.mimeType = 'image/jpeg'
    bv.byteLength = len(blob)
    bv._newblob = blob
# rebuild binary blob + bufferViews sequentially
blob_all = bytearray()
for bv in g.bufferViews:
    b = getattr(bv, '_newblob', None)
    if b is None:
        b = bytes(g.binary_blob()[bv.byteOffset:bv.byteOffset + bv.byteLength])
    bv.byteOffset = len(blob_all)
    blob_all += b
    while len(blob_all) % 4:
        blob_all += b'\x00'
g.buffers[0].byteLength = len(blob_all)
g.set_binary_blob(bytes(blob_all))
g.save('assets/model_small.glb')
sz = os.path.getsize('assets/model_small.glb')
print(f'small glb: {sz/1e6:.1f} MB')
with open('assets/model_small.glb', 'rb') as f:
    with open('assets/model.glb.b64', 'w') as o:
        o.write(base64.b64encode(f.read()).decode())
print('glb b64 written')

# ---------- 3. sample photos ----------
import glob
srcs = sorted(glob.glob('small/*.JPG')) or sorted(glob.glob('data/*.JPG'))
random.Random(3).shuffle(srcs)
for i, s in enumerate(srcs[:8]):
    im = Image.open(s)
    im.thumbnail((640, 640), Image.LANCZOS)
    out = __import__('io').BytesIO()
    im.convert('RGB').save(out, 'JPEG', quality=78)
    with open(f'assets/photo_{i}.b64', 'w') as f:
        f.write(base64.b64encode(out.getvalue()).decode())
    print('photo', i, s)
print('ASSETS DONE')
