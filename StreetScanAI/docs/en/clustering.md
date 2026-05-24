# Clustering

## Purpose
The clustering subsystem extracts object-level groups from urban LiDAR point clouds for downstream traffic interpretation, trajectory estimation, and semantic post-processing.

## Supported Methods
- `dbscan`: Open3D density-based clustering.
- `euclidean`: radius-based region-growing clustering using nearest-neighbor search.

## Key Parameters
- `eps`: DBSCAN neighborhood radius.
- `min_points`: minimum points for DBSCAN core points.
- `euclidean_tolerance`: neighbor radius for Euclidean clustering.
- `min_cluster_size`, `max_cluster_size`: cluster size filtering.
- `remove_noise`: whether label `-1` is excluded from valid cluster statistics.

## DBSCAN Usage
```bash
python src/clustering/dbscan_clustering.py \
  --input outputs/pointclouds/preprocessed/sample_preprocessed.ply \
  --output-dir outputs/clusters \
  --config configs/clustering.yaml \
  --method dbscan \
  --eps 0.8 \
  --min-points 20
```

## Euclidean Usage
```bash
python src/clustering/dbscan_clustering.py \
  --input outputs/pointclouds/preprocessed/sample_preprocessed.ply \
  --output-dir outputs/clusters \
  --method euclidean \
  --euclidean-tolerance 0.6 \
  --min-cluster-size 30
```

## CLI Integration
```bash
python src/cli.py cluster \
  --input outputs/pointclouds/preprocessed/sample_preprocessed.ply \
  --output-dir outputs/clusters \
  --method dbscan \
  --eps 0.8 \
  --min-points 20
```

## Output Files
- `outputs/clusters/<name>_clusters.ply`
- `outputs/clusters/<name>_cluster_stats.csv`
- `outputs/clusters/<name>_cluster_labels.csv`
- `outputs/reports/clustering/<name>_cluster_report.md`
- `outputs/clusters/<name>_clusters.png` (optional)

## Cluster Statistics Interpretation
- `point_count`, `centroid`: cluster size and location.
- `bbox_min/max`, `extent`, `bbox_volume`: object spatial envelope.
- `density`: approximate object compactness (`points / bbox_volume`).
- `is_noise`: identifies non-clustered points.

## Typical Starting Values
- Urban medium-density scans:
  - DBSCAN: `eps=0.6..1.0`, `min_points=15..30`
  - Euclidean: `euclidean_tolerance=0.4..0.8`, `min_cluster_size=20..50`
