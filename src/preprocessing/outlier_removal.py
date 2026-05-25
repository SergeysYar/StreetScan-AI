"""Outlier removal operations."""
from __future__ import annotations

import open3d as o3d


def remove_statistical_outliers(cloud: o3d.geometry.PointCloud, nb_neighbors: int, std_ratio: float) -> o3d.geometry.PointCloud:
    """Remove sparse statistical outliers."""
    clean, _ = cloud.remove_statistical_outlier(nb_neighbors=nb_neighbors, std_ratio=std_ratio)
    return clean


def remove_radius_outliers(cloud: o3d.geometry.PointCloud, nb_points: int, radius: float) -> o3d.geometry.PointCloud:
    """Remove outliers using radius criterion."""
    clean, _ = cloud.remove_radius_outlier(nb_points=nb_points, radius=radius)
    return clean
