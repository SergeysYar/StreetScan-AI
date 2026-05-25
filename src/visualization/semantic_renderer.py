"""Semantic point cloud rendering utilities."""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import open3d as o3d
import pandas as pd

from src.segmentation.labels import get_label_color, get_label_name
from src.visualization.pointcloud_viewer import ViewerConfig, load_cloud, render_pointcloud


def load_semantic_labels(path: Path) -> pd.DataFrame:
    """Load semantic labels CSV."""
    if not path.exists():
        raise FileNotFoundError(f"Semantic labels CSV not found: {path}")
    df = pd.read_csv(path)
    required = {"point_index", "label_id"}
    if not required.issubset(df.columns):
        raise ValueError(f"Semantic labels CSV missing required columns: {sorted(required)}")
    if "label_name" not in df.columns:
        df["label_name"] = df["label_id"].apply(lambda v: get_label_name(int(v)))
    return df


def apply_semantic_colors(cloud: o3d.geometry.PointCloud, labels_df: pd.DataFrame) -> o3d.geometry.PointCloud:
    """Apply semantic colors by per-point label_id."""
    points = np.asarray(cloud.points)
    if len(points) != len(labels_df):
        raise ValueError("Semantic labels count does not match point count.")
    out = o3d.geometry.PointCloud(cloud)
    labels_sorted = labels_df.sort_values("point_index")
    colors = np.array([get_label_color(int(v)) for v in labels_sorted["label_id"].to_numpy()], dtype=float)
    out.colors = o3d.utility.Vector3dVector(colors)
    return out


def render_semantic_cloud(cloud_path: Path, labels_path: Path, output_path: Path, config: ViewerConfig) -> None:
    """Load cloud+labels and save semantic screenshot."""
    cloud = load_cloud(cloud_path)
    labels_df = load_semantic_labels(labels_path)
    colored = apply_semantic_colors(cloud, labels_df)
    render_pointcloud(colored, output_path, config)


def create_semantic_legend(labels_df: pd.DataFrame, output_path: Path) -> None:
    """Save semantic class legend image."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    uniq = labels_df[["label_id", "label_name"]].drop_duplicates().sort_values("label_id")
    fig, ax = plt.subplots(figsize=(6, max(2, 0.35 * len(uniq))))
    ax.axis("off")
    for i, row in enumerate(uniq.itertuples(index=False)):
        c = get_label_color(int(row.label_id))
        ax.add_patch(plt.Rectangle((0, i), 0.5, 0.8, color=c))
        ax.text(0.6, i + 0.4, f"{int(row.label_id)}: {row.label_name}", va="center", fontsize=10)
    ax.set_xlim(0, 6)
    ax.set_ylim(0, len(uniq))
    ax.set_title("Semantic Legend")
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
