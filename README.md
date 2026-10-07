# DRONE → 3D

Turn drone photos into an interactive 3D model. A real photogrammetry pipeline — 61 drone photos in, an orbitable 3D building out.

**[Live demo](https://parthsingh03.github.io/Drone-to-3d/
)** — , no build step, no server needed.

## What it does

1. **Input** — 61 overlapping drone photos of a two-story building (sample photos in `sample-photos/`)
2. **Structure-from-Motion** (`pipeline/recon2.py`) — pycolmap: SIFT feature extraction, sequential matching, bundle adjustment
3. **Result** — **61/61 images registered**, **33,516 3D points**, mean reprojection error **0.42 px**
4. **Mesh** (`pipeline/build_final_glb2.py`) — reference textured mesh decimated 5.37M → 150k triangles, texture 8192 → 1024 px, repackaged as a plain `.glb`
5. **Viewer** (`pipeline/build_page.py`) — single self-contained `index.html`: photo strip, interactive point cloud, textured 3D model (Three.js, orbit/zoom), pipeline stats

## Honest notes

- The **sparse reconstruction** (camera poses + point cloud) was computed by this pipeline. The **dense textured mesh** comes from the dataset author's own multi-view-stereo reconstruction — dense MVS needs GPU muscle this pipeline didn't have. The page labels exactly what was computed vs. borrowed.
- Photogrammetry needs 60–80% overlap between consecutive photos. The first attempt (sparse temporal sampling) registered only 9/50 images; a dense consecutive window fixed it to 61/61.

## Run it yourself

```bash
pip install pycolmap pillow numpy
python pipeline/dl.py            # download the photo set (see dataset link below)
python pipeline/resize.py        # downsample for speed
python pipeline/recon2.py        # structure-from-motion → sparse point cloud
python pipeline/build_page.py    # build the viewer
```

Full-resolution run takes ~1–2 hours on a modest CPU (this was built on 2 vCPUs, no GPU).

## Dataset

Drone imagery by **Matt1up** ([drone-building-scans](https://huggingface.co/datasets/Matt1up/drone-building-scans), Hugging Face), licensed **CC BY 4.0**. If you use the imagery, credit accordingly.

## Tech

Python · pycolmap (COLMAP) · SIFT · bundle adjustment · Three.js · GLB
