"""Benchmark execution pipeline."""
from __future__ import annotations

import time
from dataclasses import dataclass

import numpy as np
import pandas as pd
import open3d as o3d

from src.benchmark.benchmark_metrics import compute_fps
from src.clustering.dbscan_clustering import run_dbscan
from src.clustering.euclidean_clustering import run_euclidean


@dataclass
class BenchmarkConfig:
    iterations: int
    methods: list[str]


def run_benchmark(cloud: o3d.geometry.PointCloud, cfg: BenchmarkConfig) -> pd.DataFrame:
    """Benchmark configured clustering methods."""
    points = np.asarray(cloud.points)
    rows: list[dict[str, float | str]] = []
    for method in cfg.methods:
        for _ in range(cfg.iterations):
            t0 = time.perf_counter()
            labels = run_dbscan(cloud, 0.8, 12) if method == "dbscan" else run_euclidean(points, 1.0, 10)
            dt = time.perf_counter() - t0
            rows.append({
                "method": method,
                "runtime": dt,
                "fps": compute_fps(dt),
                "cluster_count": float(len(set(labels.tolist()) - {-1})),
                "point_density": float(len(points) / max(1.0, points[:, :2].ptp(axis=0).prod())),
                "processing_latency": dt,
            })
    return pd.DataFrame(rows)
