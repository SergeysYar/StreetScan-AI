"""Semantic rendering utilities."""
from __future__ import annotations

import open3d as o3d

from src.segmentation.semantic_coloring import labels_to_colors


def colorize_semantic(cloud: o3d.geometry.PointCloud, labels: list[int]) -> o3d.geometry.PointCloud:
    """Apply semantic RGB colors to cloud."""
    cloud.colors = o3d.utility.Vector3dVector(labels_to_colors(labels))
    return cloud
