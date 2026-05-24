"""Preprocessing pipeline."""
from __future__ import annotations

from dataclasses import dataclass

import open3d as o3d

from src.preprocessing.ground_filter import estimate_ground_plane, filter_ground
from src.preprocessing.normalization import normalize_cloud
from src.preprocessing.outlier_removal import remove_radius_outliers, remove_statistical_outliers
from src.preprocessing.voxel_downsampling import voxel_downsample


@dataclass
class PreprocessConfig:
    voxel_size: float = 0.2
    sor_nb_neighbors: int = 20
    sor_std_ratio: float = 2.0
    radius_nb_points: int = 8
    radius: float = 0.6
    normalize: bool = True
    center: bool = True
    ground_distance_threshold: float = 0.25


def run_preprocessing(cloud: o3d.geometry.PointCloud, cfg: PreprocessConfig) -> o3d.geometry.PointCloud:
    """Run full preprocessing pipeline."""
    cloud = voxel_downsample(cloud, cfg.voxel_size)
    cloud = remove_statistical_outliers(cloud, cfg.sor_nb_neighbors, cfg.sor_std_ratio)
    cloud = remove_radius_outliers(cloud, cfg.radius_nb_points, cfg.radius)
    _, inliers = estimate_ground_plane(cloud, cfg.ground_distance_threshold)
    cloud = filter_ground(cloud, inliers, keep_ground=False)
    if cfg.normalize:
        cloud = normalize_cloud(cloud, center=cfg.center)
    return cloud
