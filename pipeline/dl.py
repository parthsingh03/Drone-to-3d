from huggingface_hub import hf_hub_download
import os, sys
imgs = [l.strip() for l in open('/tmp/shingle_imgs.txt') if l.strip()]
sel = imgs[::8]
print('selected', len(sel), 'images', flush=True)
os.makedirs('data', exist_ok=True)
for i, p in enumerate(sel):
    name = os.path.basename(p)
    dst = f'data/{name}'
    if not os.path.exists(dst):
        try:
            hf_hub_download('Matt1up/drone-building-scans', filename=p, repo_type='dataset',
                            local_dir='.', local_dir_use_symlinks=False)
            # hf_hub_download puts it under ./shingle-roof/images/...; move to data/
            os.rename(p, dst)
            print(f'[{i+1}/{len(sel)}] {name}', flush=True)
        except Exception as e:
            print(f'FAIL {name}: {e}', flush=True)
    else:
        print(f'[{i+1}/{len(sel)}] {name} (cached)', flush=True)
g = 'shingle-roof/model/shingle-roof.glb'
if not os.path.exists('data/shingle-roof.glb'):
    hf_hub_download('Matt1up/drone-building-scans', filename=g, repo_type='dataset',
                    local_dir='.', local_dir_use_symlinks=False)
    os.rename(g, 'data/shingle-roof.glb')
    print('glb OK', flush=True)
print('DOWNLOAD DONE', flush=True)
