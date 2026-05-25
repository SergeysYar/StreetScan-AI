import numpy as np

from src.utils.geometry_utils import axis_aligned_bbox, normalize_points


def test_bbox_size():
    points = np.array([[0, 0, 0], [2, 3, 4]])
    bbox = axis_aligned_bbox(points)
    assert np.allclose(bbox["size"], [2, 3, 4])


def test_normalize_points_max_norm():
    points = np.array([[1.0, 0.0, 0.0], [0.0, 2.0, 0.0]])
    normed = normalize_points(points)
    assert np.isclose(np.linalg.norm(normed, axis=1).max(), 1.0)
