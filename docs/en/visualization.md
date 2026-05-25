# Visualization

## Purpose
Visualization renders StreetScanAI outputs into portfolio-ready screenshots, plots, and optional animations.

## Supported Inputs
- Required: point cloud (`.ply`, `.pcd`, `.xyz`)
- Optional:
  - semantic labels CSV
  - cluster labels CSV
  - density grid CSV
  - occupancy grid CSV
  - trajectory CSV

## Rendering Modes
- Point cloud screenshot
- Semantic rendering by class labels
- Cluster rendering by cluster ID
- Bird-eye density view
- Density heatmap / occupancy map
- Trajectory rendering (2D)
- Optional turntable GIF export

## Output Files
- `outputs/visualizations/<name>_pointcloud.png`
- `outputs/visualizations/<name>_semantic.png`
- `outputs/visualizations/<name>_clusters.png`
- `outputs/visualizations/<name>_bird_eye.png`
- `outputs/visualizations/<name>_density_heatmap.png`
- `outputs/visualizations/<name>_trajectories.png`
- `outputs/visualizations/<name>_turntable.gif` (optional)
- `outputs/reports/visualization/<name>_visualization_report.md`

## Config Example
```yaml
visualization:
  backend: open3d
  image_width: 1600
  image_height: 1000
  point_size: 2.0
  background_color: [1.0, 1.0, 1.0]
  camera_view: isometric
  save_animation: false
  animation_frames: 60
  animation_fps: 20
  bird_eye_resolution: 0.2
  plot_dpi: 150
  show_axes: true
```

## CLI Examples
```bash
uv run src/visualization/visualization_pipeline.py \
  --input outputs/pointclouds/preprocessed/sample_preprocessed.ply \
  --output-dir outputs/visualizations \
  --config configs/visualization.yaml
```

```bash
uv run src/cli.py visualize \
  --input outputs/pointclouds/preprocessed/sample_preprocessed.ply \
  --semantic-labels outputs/semantic/sample_semantic_labels.csv \
  --cluster-labels outputs/clusters/sample_cluster_labels.csv \
  --trajectories outputs/trajectories/sample_tracked_objects.csv \
  --output-dir outputs/visualizations \
  --camera-view isometric \
  --save-animation
```

## Headless and Limitations
- In headless systems, off-screen rendering may fail for some backends; pipeline continues with warnings.
- GIF export needs `imageio`; otherwise frame sequence is kept and warning is reported.

