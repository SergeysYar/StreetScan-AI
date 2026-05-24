"""DBSCAN clustering for point clouds."""
from __future__ import annotations

import numpy as np
import open3d as o3d


def run_dbscan(cloud: o3d.geometry.PointCloud, eps: float, min_points: int) -> np.ndarray:
    """Run Open3D DBSCAN and return labels."""
    labels = np.array(cloud.cluster_dbscan(eps=eps, min_points=min_points, print_progress=False))
    return labels
