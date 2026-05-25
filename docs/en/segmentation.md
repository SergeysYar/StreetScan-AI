# Segmentation

## Purpose
The semantic segmentation subsystem assigns point-wise urban classes for downstream perception and analysis.

## Supported Classes
- `0 unlabeled`
- `1 road`
- `2 building`
- `3 vehicle`
- `4 pedestrian`
- `5 vegetation`
- `6 pole`
- `7 traffic_sign`

## Baseline Method
`baseline` mode is deterministic and rule-based:
- height normalization from minimum Z
- near-ground assignment to `road`
- height range rules for `vehicle` and `pedestrian`
- elevated structures split into `building`/`vegetation` via local density
- narrow elevated structures mapped to `pole`/`traffic_sign`

This is an explainable baseline, not a trained neural model.

## PointNet++ Placeholder
`pointnet` mode is an integration contract. If weights are missing, execution fails with an explicit error.
No fake neural predictions are generated.

## Input / Output
- Input: `.ply`, `.pcd`, `.xyz`
- Output:
  - `outputs/semantic/<name>_semantic.ply`
  - `outputs/semantic/<name>_semantic_labels.csv`
  - `outputs/semantic/<name>_semantic_stats.csv`
  - `outputs/reports/segmentation/<name>_segmentation_report.md`
  - optional `outputs/semantic/<name>_semantic.png`

## Config Example
```yaml
segmentation:
  method: baseline
  weights_path: null
  device: cpu
  use_cluster_features: false
  cluster_labels_path: null
  cluster_stats_path: null
  z_ground_threshold: 0.25
  z_vehicle_min: 0.3
  z_vehicle_max: 2.2
  z_pedestrian_min: 0.5
  z_pedestrian_max: 2.5
  pole_radius_threshold: 0.25
  min_points_per_object: 20
  save_screenshot: false
  output_format: ply
```

## CLI Examples
```bash
python src/segmentation/semantic_segmentation.py \
  --input outputs/pointclouds/preprocessed/sample_preprocessed.ply \
  --output-dir outputs/semantic \
  --method baseline
```

```bash
python src/cli.py segment \
  --input outputs/pointclouds/preprocessed/sample_preprocessed.ply \
  --output-dir outputs/semantic \
  --method baseline \
  --config configs/segmentation.yaml
```

## Limitations and Future Work
- Baseline rules are scene-dependent and limited in accuracy.
- PointNet++ path is a placeholder until real trained model integration is added.
