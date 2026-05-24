"""Semantic coloring utilities."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import open3d as o3d
import pandas as pd

from src.segmentation.labels import get_label_color, get_label_name
from src.segmentation.segmentation_io import save_point_cloud


def colorize_by_labels(cloud: o3d.geometry.PointCloud, labels: np.ndarray) -> o3d.geometry.PointCloud:
    """Return a copy of cloud with semantic colors assigned by labels."""
    points = np.asarray(cloud.points)
    if len(points) != len(labels):
        raise ValueError("Labels length does not match number of points in cloud.")
    colored = o3d.geometry.PointCloud(cloud)
    colors = np.array([get_label_color(int(label)) for label in labels], dtype=float)
    colored.colors = o3d.utility.Vector3dVector(colors)
    return colored


def save_semantic_cloud(cloud: o3d.geometry.PointCloud, labels: np.ndarray, output_path: Path) -> None:
    """Colorize and save semantic point cloud."""
    colored = colorize_by_labels(cloud, labels)
    save_point_cloud(colored, output_path)


def create_legend_table(labels: np.ndarray) -> pd.DataFrame:
    """Create semantic legend/count table from labels."""
    unique, counts = np.unique(labels, return_counts=True)
    rows = []
    for label_id, count in zip(unique.tolist(), counts.tolist()):
        rows.append(
            {
                "label_id": int(label_id),
                "label_name": get_label_name(int(label_id)),
                "color_rgb": str(get_label_color(int(label_id))),
                "points": int(count),
            }
        )
    return pd.DataFrame(rows).sort_values("label_id").reset_index(drop=True)
