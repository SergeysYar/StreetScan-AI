# Tracking

## Purpose
Tracking reconstructs dynamic object trajectories across frames from detection/cluster centroids.

## Input CSV Format
Required columns:
- `frame_id`, `x`, `y`, `z`

Optional columns:
- `timestamp`, `object_id`, `class_name`, `confidence`
- bounding box columns (`bbox_min_*`, `bbox_max_*`)

If timestamps are missing, time is derived from `fps`.
If classes are missing, `default_class_name` is used.

## Method Overview
- Frame-to-frame nearest-neighbor association in XYZ.
- Optional Hungarian assignment when `scipy` is available.
- Constant-velocity Kalman filter (`[x,y,z,vx,vy,vz]`) when enabled.
- Trajectory pruning by `min_track_length`.
- Optional moving-average smoothing for `x,y,z`.

## Velocity Estimation
- Uses timestamp deltas when available.
- Falls back to `dt = 1/fps`.
- Outputs `vx, vy, vz, speed`.

## Outputs
- `outputs/trajectories/<name>_tracked_objects.csv`
- `outputs/trajectories/<name>_trajectory_summary.csv`
- `outputs/plots/trajectories/<name>_trajectories_xy.png`
- `outputs/plots/trajectories/<name>_velocity.png`
- `outputs/trajectories/<name>_trajectory_overlay.ply` (optional)
- `outputs/reports/tracking/<name>_tracking_report.md`

## Config Example
```yaml
tracking:
  fps: 10.0
  association_distance_threshold: 2.0
  max_missed_frames: 5
  min_track_length: 3
  enable_kalman_filter: true
  enable_smoothing: true
  smoothing_window: 5
  plot_dpi: 150
  save_overlay_cloud: true
  default_class_name: unknown
```

## CLI Examples
```bash
python src/tracking/tracking_pipeline.py \
  --input data/trajectories/urban_detections.csv \
  --output-dir outputs/trajectories \
  --config configs/tracking.yaml
```

```bash
python src/cli.py track \
  --input data/trajectories/urban_detections.csv \
  --output-dir outputs/trajectories \
  --fps 10 \
  --association-distance 2.0 \
  --save-overlay-cloud
```

## Limitations
- Association is geometric and may fail with long occlusions.
- Quality depends on input detection consistency and frame rate.
