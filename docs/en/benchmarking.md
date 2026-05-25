# Benchmarking

## Purpose
The benchmarking subsystem compares preprocessing, clustering, and segmentation configurations on identical LiDAR inputs for reproducible engineering evaluation.

## Supported Modes
- `preprocessing`
- `clustering`
- `segmentation`

## Input Data
- Required: point cloud file or directory (`.ply`, `.pcd`, `.xyz`)
- Optional: semantic ground-truth labels CSV (`--ground-truth-labels`)

## Config Overview
`configs/benchmark.yaml` defines:
- mode selection
- warmup + measured repetitions
- preprocessing/clustering/segmentation experiment grids
- random seed and output paths

## Output Files
- `outputs/benchmarks/benchmark_results.csv`
- `outputs/benchmarks/benchmark_summary.json`
- `outputs/reports/benchmark/benchmark_report.md`
- `outputs/plots/benchmarks/runtime_comparison.png`
- `outputs/plots/benchmarks/points_per_second.png`
- `outputs/plots/benchmarks/point_count_reduction.png`
- `outputs/plots/benchmarks/cluster_quality.png`
- `outputs/plots/benchmarks/segmentation_accuracy.png`
- `outputs/benchmarks/runs/<run_id>/run_metadata.json`
- `outputs/benchmarks/runs/<run_id>/metrics.json`

## Metric Notes
- Runtime metrics are aggregated across repetitions (`mean/std/min/max`).
- Throughput is reported as points per second.
- Cluster quality uses statistics from generated cluster tables.
- Segmentation accuracy is computed only when valid ground truth is available.

## CLI Examples
```bash
python src/benchmark/benchmark_runner.py \
  --input data/raw/sample.ply \
  --output-dir outputs/benchmarks \
  --config configs/benchmark.yaml \
  --modes preprocessing clustering segmentation \
  --repetitions 3
```

```bash
python src/cli.py benchmark \
  --input data/raw/sample.ply \
  --output-dir outputs/benchmarks \
  --modes preprocessing clustering \
  --repetitions 3
```

## Limitations
- Accuracy metrics are unavailable when ground-truth labels are missing or mismatched.
- Failed experiments are preserved in CSV/report and do not stop remaining runs.
