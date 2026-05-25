"""Ground plane filtering."""
from __future__ import annotations

import open3d as o3d


def estimate_ground_plane(cloud: o3d.geometry.PointCloud, distance_threshold: float = 0.25) -> tuple[list[float], list[int]]:
    """Estimate ground plane with RANSAC."""
    model, inliers = cloud.segment_plane(distance_threshold=distance_threshold, ransac_n=3, num_iterations=500)
    return model, inliers


def filter_ground(cloud: o3d.geometry.PointCloud, inliers: list[int], keep_ground: bool = False) -> o3d.geometry.PointCloud:
    """Remove or isolate ground inliers."""
    return cloud.select_by_index(inliers, invert=not keep_ground)
