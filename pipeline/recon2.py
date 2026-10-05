"""Re-run incremental mapping on the existing recon.db with aerial-friendly tuning."""
import pycolmap
from pathlib import Path

img_dir = Path('small')
db_path = Path('recon.db')
out_dir = Path('sparse2')
out_dir.mkdir(exist_ok=True)

pipeline = pycolmap.IncrementalPipelineOptions(num_threads=2)
pipeline.init_num_trials = 400
pipeline.mapper.init_min_tri_angle = 8.0
pipeline.mapper.init_max_forward_motion = 0.99
pipeline.mapper.abs_pose_min_num_inliers = 20
pipeline.mapper.abs_pose_min_inlier_ratio = 0.2
pipeline.mapper.filter_max_reproj_error = 6.0
pipeline.mapper.max_reg_trials = 5

recs = pycolmap.incremental_mapping(db_path, img_dir, out_dir, pipeline)
print(f'models found: {len(recs)}', flush=True)
best = None
for k, r in recs.items():
    n_img, n_pts = r.num_reg_images(), r.num_points3D()
    print(f'model {k}: registered images={n_img} points3D={n_pts}', flush=True)
    if best is None or n_img > best[1]:
        best = (k, n_img, r)
if best is None:
    print('RECONSTRUCTION FAILED')
    raise SystemExit(1)
k, n_img, rec = best
rec.export_PLY('sparse_cloud.ply')
print(f'FINAL: {n_img} registered images, {rec.num_points3D()} points -> sparse_cloud.ply', flush=True)
