"""Cluster point cloud rendering utilities."""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import open3d as o3d
import pandas as pd

from src.visualization.pointcloud_viewer import ViewerConfig, load_cloud, render_pointcloud


def load_cluster_labels(path: Path) -> pd.DataFrame:
    """Load cluster labels CSV."""
    if not path.exists():
        raise FileNotFoundError(f"Cluster labels CSV not found: {path}")
    df = pd.read_csv(path)
    required = {"point_index", "cluster_label"}
    if not required.issubset(df.columns):
        raise ValueError(f"Cluster labels CSV missing required columns: {sorted(required)}")
    if "is_noise" not in df.columns:
        df["is_noise"] = df["cluster_label"] == -1
    return df


def apply_cluster_colors(cloud: o3d.geometry.PointCloud, cluster_df: pd.DataFrame) -> o3d.geometry.PointCloud:
    """Apply deterministic colors per cluster id; noise in gray."""
    pts = np.asarray(cloud.points)
    if len(pts) != len(cluster_df):
        raise ValueError("Cluster labels count does not match point count.")
    df = cluster_df.sort_values("point_index")
    labels = df["cluster_label"].to_numpy(dtype=int)
    rng = np.random.default_rng(42)
    unique = sorted(set(int(v) for v in labels if v >= 0))
    palette = {u: rng.random(3) for u in unique}
    colors = np.zeros((len(labels), 3), dtype=float)
    for i, lid in enumerate(labels):
        colors[i] = np.array([0.5, 0.5, 0.5]) if lid < 0 else palette[int(lid)]
    out = o3d.geometry.PointCloud(cloud)
    out.colors = o3d.utility.Vector3dVector(colors)
    return out


def render_cluster_cloud(cloud_path: Path, cluster_labels_path: Path, output_path: Path, config: ViewerConfig) -> None:
    """Render cluster-colored cloud screenshot."""
    cloud = load_cloud(cloud_path)
    cdf = load_cluster_labels(cluster_labels_path)
    colored = apply_cluster_colors(cloud, cdf)
    render_pointcloud(colored, output_path, config)


def create_cluster_legend(cluster_df: pd.DataFrame, output_path: Path) -> None:
    """Save cluster legend image for cluster IDs."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    ids = sorted(set(int(v) for v in cluster_df["cluster_label"].tolist()))
    rng = np.random.default_rng(42)
    uniq = sorted([i for i in ids if i >= 0])
    palette = {u: rng.random(3) for u in uniq}

    fig, ax = plt.subplots(figsize=(6, max(2, 0.3 * len(ids))))
    ax.axis("off")
    row = 0
    for lid in ids:
        c = (0.5, 0.5, 0.5) if lid < 0 else tuple(palette[lid])
        ax.add_patch(plt.Rectangle((0, row), 0.5, 0.8, color=c))
        ax.text(0.6, row + 0.4, f"cluster {lid}", va="center")
        row += 1
    ax.set_xlim(0, 4)
    ax.set_ylim(0, max(1, row))
    ax.set_title("Cluster Legend")
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
