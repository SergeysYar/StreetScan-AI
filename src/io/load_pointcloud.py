"""Point cloud loading."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import open3d as o3d

from src.io.formats import validate_format


def load_point_cloud(path: Path) -> o3d.geometry.PointCloud:
    """Load point cloud from supported format."""
    validate_format(path)
    if path.suffix.lower() == ".las":
        raise NotImplementedError("LAS loader placeholder. Integrate laspy in future.")
    cloud = o3d.io.read_point_cloud(str(path))
    if cloud.is_empty():
        raise ValueError(f"Loaded empty point cloud: {path}")
    return cloud


def to_numpy(cloud: o3d.geometry.PointCloud) -> tuple[np.ndarray, np.ndarray | None]:
    """Convert Open3D cloud to numpy arrays."""
    points = np.asarray(cloud.points)
    colors = np.asarray(cloud.colors) if cloud.has_colors() else None
    return points, colors
