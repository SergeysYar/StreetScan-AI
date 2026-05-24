"""Point cloud normalization."""
from __future__ import annotations

import numpy as np
import open3d as o3d

from src.utils.geometry_utils import center_points, normalize_points


def normalize_cloud(cloud: o3d.geometry.PointCloud, center: bool = True) -> o3d.geometry.PointCloud:
    """Normalize and optionally center cloud coordinates."""
    points = np.asarray(cloud.points)
    points = center_points(points) if center else points
    points = normalize_points(points)
    cloud.points = o3d.utility.Vector3dVector(points)
    return cloud
