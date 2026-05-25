# Analytics

## Purpose
Urban analytics converts LiDAR point clouds and optional semantic/cluster/trajectory data into interpretable spatial metrics for smart city and autonomy diagnostics.

## Inputs
- Required: point cloud (`.ply`, `.pcd`, `.xyz`)
- Optional:
  - semantic labels CSV
  - cluster stats CSV
  - trajectory CSV

## Core Analytics
- Density heatmap on XY grid
- Occupancy grid and occupancy ratio
- Traffic summary (semantic/cluster fallback)
- Pedestrian flow/concentration (trajectory-aware)
- Approximate radial visibility profile
- Global spatial statistics

## Output Files
- `outputs/plots/analytics/<name>_density_heatmap.png`
- `outputs/analytics/<name>_occupancy_grid.csv`
- `outputs/plots/analytics/<name>_occupancy_map.png`
- `outputs/analytics/<name>_spatial_statistics.csv`
- `outputs/analytics/<name>_traffic_summary.csv`
- `outputs/analytics/<name>_pedestrian_flow.csv`
- `outputs/analytics/<name>_visibility.csv`
- `outputs/reports/analytics/<name>_analytics_report.md`

## Config Example
```yaml
analytics:
  grid_resolution: 0.5
  density_normalization: true
  occupancy_threshold: 1
  max_range: 80.0
  sensor_origin: [0.0, 0.0, 0.0]
  visibility_angle_step_deg: 1.0
  visibility_range_bins: 80
  save_plots: true
  plot_dpi: 150
  semantic_labels_path: null
  cluster_stats_path: null
  trajectory_path: null
```

## CLI Examples
```bash
uv run src/analytics/analytics_pipeline.py \
  --input outputs/pointclouds/preprocessed/sample_preprocessed.ply \
  --output-dir outputs/analytics \
  --config configs/analytics.yaml
```

```bash
uv run src/cli.py analyze \
  --input outputs/pointclouds/preprocessed/sample_preprocessed.ply \
  --output-dir outputs/analytics \
  --semantic-labels outputs/semantic/sample_semantic_labels.csv \
  --cluster-stats outputs/clusters/sample_cluster_stats.csv \
  --grid-resolution 0.5 \
  --save-plots
```

## Limitations
- Visibility profile is approximate radial coverage, not full ray tracing.
- Traffic and pedestrian metrics become heuristic if optional labels/trajectories are missing.

