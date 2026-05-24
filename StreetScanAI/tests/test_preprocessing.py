import numpy as np
import open3d as o3d

from src.preprocessing.preprocess_pipeline import PreprocessConfig, run_preprocessing


def test_preprocessing_returns_cloud():
    points = np.random.randn(200, 3)
    cloud = o3d.geometry.PointCloud()
    cloud.points = o3d.utility.Vector3dVector(points)
    cfg = PreprocessConfig(voxel_size=0.2)
    out = run_preprocessing(cloud, cfg)
    assert isinstance(out, o3d.geometry.PointCloud)
