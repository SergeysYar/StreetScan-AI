# Preprocessing

## Purpose
The preprocessing subsystem prepares raw urban LiDAR clouds for downstream clustering, segmentation, analytics, and visualization by reducing noise and normalizing geometry.

## Supported Formats
- Input: `.ply`, `.pcd`, `.xyz`
- Output: `.ply` or `.pcd` (configurable)

## Available Operations
- Voxel downsampling
- Statistical outlier removal
- Radius outlier removal
- RANSAC ground plane estimation and split (ground/non-ground)
- Coordinate normalization (centroid translation only)
- Approximate point density estimation (`points / AABB volume`)

## Configuration Example
```yaml
preprocessing:
  voxel_size: 0.1
  enable_voxel_downsampling: true
  enable_statistical_outlier_removal: true
  statistical_nb_neighbors: 20
  statistical_std_ratio: 2.0
  enable_radius_outlier_removal: false
  radius_nb_points: 8
  radius: 0.5
  enable_ground_filtering: true
  ground_distance_threshold: 0.2
  ground_ransac_n: 3
  ground_num_iterations: 1000
  normalize_coordinates: false
  estimate_density: true
  output_format: ply
```

## CLI Usage
```bash
uv run src/preprocessing/preprocess_pointcloud.py \
  --input data/raw/sample.ply \
  --output-dir outputs/pointclouds/preprocessed \
  --config configs/preprocessing.yaml
```

```bash
uv run src/cli.py preprocess \
  --input data/raw/sample.ply \
  --output-dir outputs/pointclouds/preprocessed \
  --ground-filter \
  --estimate-density
```

## Output Files
- `outputs/pointclouds/preprocessed/<name>_preprocessed.(ply|pcd)`
- `outputs/pointclouds/preprocessed/<name>_ground.(ply|pcd)` (if enabled)
- `outputs/pointclouds/preprocessed/<name>_nonground.(ply|pcd)` (if enabled)
- `outputs/reports/preprocessing/<name>_stats.json`
- `outputs/reports/preprocessing/<name>_report.md`

## Statistics Interpretation
- `original_points`, `after_downsampling_points`, `after_outlier_removal_points`, `final_points`: reduction profile
- `ground_points` / `nonground_points`: split quality for ground filtering
- `bounding_box_*`, `centroid`: geometric envelope and position
- `average_density`: approximate volumetric density; `null` means invalid/zero volume
- `operations_applied` and `warnings`: traceability and failure diagnostics

