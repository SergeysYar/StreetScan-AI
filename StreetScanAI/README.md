# StreetScanAI

[![Build](https://img.shields.io/badge/build-placeholder-blue)](#)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-orange)](#)

StreetScanAI is a production-oriented LiDAR perception and urban 3D analytics framework for semantic point-cloud understanding, clustering, trajectory analysis, and benchmarking.

## Architecture
- `src/io`: format-aware cloud loading/saving (`.ply`, `.pcd`, `.xyz`, `.las` placeholder)
- `src/preprocessing`: voxel filtering, outlier removal, normalization, ground filtering
- `src/clustering`: DBSCAN, Euclidean clustering, cluster statistics
- `src/segmentation`: semantic labels and PointNet++ integration interface
- `src/tracking`: trajectory building, velocity estimation, Kalman placeholder
- `src/analytics`: density, occupancy, traffic, visibility, spatial statistics
- `src/visualization`: heatmaps, semantic render helpers, trajectory plotting
- `src/benchmark`: repeatable runtime and metric benchmarking
- `src/cli.py`: unified production-style command interface

## Installation
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
```

## Quick start
```bash
cd StreetScanAI
python -m src.cli preprocess --config configs/config.yaml --input data/raw/sample.ply
python -m src.cli cluster --config configs/config.yaml --input outputs/pointclouds/preprocessed.ply
python -m src.cli segment --config configs/config.yaml --input outputs/pointclouds/preprocessed.ply
python -m src.cli analyze --config configs/config.yaml --input outputs/pointclouds/preprocessed.ply
python -m src.cli benchmark --config configs/config.yaml --input outputs/pointclouds/preprocessed.ply
```

## Visual Outputs
- Demo GIF: `assets/demo.gif`
- Semantic rendering: `assets/semantic_example.png`
- Clustering result: `assets/clustering_example.png`
- Trajectory view: `assets/trajectory_example.png`
- Benchmark chart: `assets/benchmark_example.png`

## Roadmap
1. Add LAS/LAZ via `laspy` integration.
2. Integrate PointNet++/Minkowski backbones.
3. Add multi-frame data association and MOT metrics.
4. Add CI + containerized benchmarks.

## License
MIT. See [LICENSE](LICENSE).
