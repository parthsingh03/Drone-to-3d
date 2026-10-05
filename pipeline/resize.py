"""Downsample data/*.JPG to max 1024px into small/ (keeps aspect, preserves EXIF for focal length)."""
from PIL import Image
import os, glob

os.makedirs('small', exist_ok=True)
srcs = sorted(glob.glob('data/*.JPG'))
for i, src in enumerate(srcs):
    dst = 'small/' + os.path.basename(src)
    if os.path.exists(dst):
        print(f'[{i+1}/{len(srcs)}] {os.path.basename(dst)} (cached)')
        continue
    im = Image.open(src)
    exif = im.info.get('exif')
    im.thumbnail((1024, 1024), Image.LANCZOS)
    kw = {'quality': 90}
    if exif:
        kw['exif'] = exif
    im.save(dst, 'JPEG', **kw)
    print(f'[{i+1}/{len(srcs)}] {os.path.basename(dst)} {im.size}', flush=True)
print('RESIZE DONE')
