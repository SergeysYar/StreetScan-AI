"""Voxel downsampling."""
from __future__ import annotations

import open3d as o3d


def voxel_downsample(cloud: o3d.geometry.PointCloud, voxel_size: float) -> o3d.geometry.PointCloud:
    """Apply voxel downsampling."""
    return cloud.voxel_down_sample(voxel_size=voxel_size)
