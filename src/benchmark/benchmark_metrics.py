"""Reusable metric functions for benchmark subsystem."""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def compute_runtime_stats(times: list[float]) -> dict[str, float]:
    """Compute runtime aggregation statistics."""
    if len(times) == 0:
        return {"runtime_mean_sec": np.nan, "runtime_std_sec": np.nan, "runtime_min_sec": np.nan, "runtime_max_sec": np.nan}
    arr = np.array(times, dtype=float)
    return {
        "runtime_mean_sec": float(arr.mean()),
        "runtime_std_sec": float(arr.std(ddof=0)),
        "runtime_min_sec": float(arr.min()),
        "runtime_max_sec": float(arr.max()),
    }


def compute_points_per_second(point_count: int, runtime_sec: float) -> float:
    """Compute throughput as points per second."""
    if runtime_sec <= 0:
        return float("nan")
    return float(point_count / runtime_sec)


def compute_point_reduction_ratio(original_points: int, processed_points: int) -> float:
    """Compute reduction ratio (0..1) after preprocessing."""
    if original_points <= 0:
        return float("nan")
    return float((original_points - processed_points) / original_points)


def compute_cluster_quality(cluster_stats: pd.DataFrame) -> dict[str, Any]:
    """Compute cluster quality summary metrics from cluster stats table."""
    if cluster_stats is None or cluster_stats.empty:
        return {
            "number_of_clusters": np.nan,
            "noise_ratio": np.nan,
            "mean_cluster_size": np.nan,
            "median_cluster_size": np.nan,
            "max_cluster_size": np.nan,
            "min_cluster_size": np.nan,
            "cluster_size_std": np.nan,
        }

    if "point_count" in cluster_stats.columns:
        sizes = pd.to_numeric(cluster_stats["point_count"], errors="coerce").dropna().to_numpy(dtype=float)
    elif "num_points" in cluster_stats.columns:
        sizes = pd.to_numeric(cluster_stats["num_points"], errors="coerce").dropna().to_numpy(dtype=float)
    else:
        sizes = np.array([], dtype=float)

    noise_ratio = np.nan
    if "is_noise" in cluster_stats.columns:
        noise_ratio = float(pd.to_numeric(cluster_stats["is_noise"], errors="coerce").fillna(0).mean())

    if len(sizes) == 0:
        return {
            "number_of_clusters": float(cluster_stats.shape[0]),
            "noise_ratio": noise_ratio,
            "mean_cluster_size": np.nan,
            "median_cluster_size": np.nan,
            "max_cluster_size": np.nan,
            "min_cluster_size": np.nan,
            "cluster_size_std": np.nan,
        }

    return {
        "number_of_clusters": float(len(sizes)),
        "noise_ratio": noise_ratio,
        "mean_cluster_size": float(np.mean(sizes)),
        "median_cluster_size": float(np.median(sizes)),
        "max_cluster_size": float(np.max(sizes)),
        "min_cluster_size": float(np.min(sizes)),
        "cluster_size_std": float(np.std(sizes, ddof=0)),
    }


def compute_segmentation_accuracy(pred_labels: np.ndarray, gt_labels: np.ndarray, ignore_unlabeled: bool = True) -> dict[str, Any]:
    """Compute segmentation accuracy metrics using predicted and ground-truth labels."""
    if pred_labels.shape[0] != gt_labels.shape[0]:
        raise ValueError("Predicted and ground-truth label arrays must have same length")

    mask = np.ones_like(gt_labels, dtype=bool)
    if ignore_unlabeled:
        mask = gt_labels != 0
    ignored = int((~mask).sum())

    pred = pred_labels[mask]
    gt = gt_labels[mask]
    if gt.shape[0] == 0:
        return {
            "overall_accuracy": np.nan,
            "per_class_accuracy": {},
            "mean_class_accuracy": np.nan,
            "labeled_point_count": 0,
            "ignored_point_count": ignored,
        }

    overall = float((pred == gt).sum() / gt.shape[0])
    classes = sorted(set(gt.tolist()))
    per_class: dict[int, float] = {}
    for cls in classes:
        c_mask = gt == cls
        per_class[int(cls)] = float((pred[c_mask] == gt[c_mask]).sum() / max(1, c_mask.sum()))

    return {
        "overall_accuracy": overall,
        "per_class_accuracy": per_class,
        "mean_class_accuracy": float(np.mean(list(per_class.values()))) if per_class else np.nan,
        "labeled_point_count": int(gt.shape[0]),
        "ignored_point_count": ignored,
    }


def summarize_benchmark_rows(rows: list[dict[str, Any]]) -> pd.DataFrame:
    """Create pandas table from benchmark row dictionaries."""
    return pd.DataFrame(rows)


def compute_fps(runtime_sec: float) -> float:
    """Backward-compatible FPS helper."""
    return 0.0 if runtime_sec <= 0 else 1.0 / runtime_sec
