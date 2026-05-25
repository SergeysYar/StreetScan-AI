"""Benchmark plotting utilities (matplotlib only)."""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def _bar(df: pd.DataFrame, x: str, y: str, title: str, ylabel: str, output_path: Path, dpi: int = 150) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(df[x].astype(str), pd.to_numeric(df[y], errors="coerce"), color="#2563eb")
    ax.set_title(title)
    ax.set_xlabel("Experiment")
    ax.set_ylabel(ylabel)
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()
    fig.savefig(output_path, dpi=dpi)
    plt.close(fig)


def plot_runtime_comparison(df: pd.DataFrame, output_path: Path, dpi: int = 150) -> None:
    """Plot runtime comparison."""
    if "runtime_mean_sec" not in df.columns:
        return
    _bar(df, "experiment_name", "runtime_mean_sec", "Runtime Comparison", "Runtime (s)", output_path, dpi)


def plot_points_per_second(df: pd.DataFrame, output_path: Path, dpi: int = 150) -> None:
    """Plot points-per-second comparison."""
    if "points_per_second" not in df.columns:
        return
    _bar(df, "experiment_name", "points_per_second", "Points per Second", "Points/s", output_path, dpi)


def plot_point_reduction(df: pd.DataFrame, output_path: Path, dpi: int = 150) -> None:
    """Plot preprocessing point reduction ratios."""
    if "point_reduction_ratio" not in df.columns:
        return
    sub = df[df["mode"] == "preprocessing"] if "mode" in df.columns else df
    if sub.empty:
        return
    _bar(sub, "experiment_name", "point_reduction_ratio", "Point Count Reduction", "Reduction Ratio", output_path, dpi)


def plot_cluster_quality(df: pd.DataFrame, output_path: Path, dpi: int = 150) -> None:
    """Plot cluster quality proxy (number_of_clusters)."""
    if "number_of_clusters" not in df.columns:
        return
    sub = df[df["mode"] == "clustering"] if "mode" in df.columns else df
    if sub.empty:
        return
    _bar(sub, "experiment_name", "number_of_clusters", "Cluster Quality Proxy", "Cluster Count", output_path, dpi)


def plot_segmentation_accuracy(df: pd.DataFrame, output_path: Path, dpi: int = 150) -> None:
    """Plot segmentation accuracy if available."""
    if "segmentation_accuracy" not in df.columns:
        return
    sub = df[df["mode"] == "segmentation"] if "mode" in df.columns else df
    sub = sub.dropna(subset=["segmentation_accuracy"])
    if sub.empty:
        return
    _bar(sub, "experiment_name", "segmentation_accuracy", "Segmentation Accuracy", "Accuracy", output_path, dpi)


def generate_all_plots(df: pd.DataFrame, output_dir: Path, dpi: int = 150) -> list[Path]:
    """Generate all benchmark comparison plots."""
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = [
        output_dir / "runtime_comparison.png",
        output_dir / "points_per_second.png",
        output_dir / "point_count_reduction.png",
        output_dir / "cluster_quality.png",
        output_dir / "segmentation_accuracy.png",
    ]
    plot_runtime_comparison(df, paths[0], dpi=dpi)
    plot_points_per_second(df, paths[1], dpi=dpi)
    plot_point_reduction(df, paths[2], dpi=dpi)
    plot_cluster_quality(df, paths[3], dpi=dpi)
    plot_segmentation_accuracy(df, paths[4], dpi=dpi)
    return [p for p in paths if p.exists()]
