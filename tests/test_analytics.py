import numpy as np

from src.analytics.density_analysis import density_histogram
from src.analytics.visibility_analysis import visible_ratio


def test_density_histogram_non_empty():
    points = np.random.rand(100, 3)
    hist, _, _ = density_histogram(points, resolution=0.1)
    assert hist.sum() == 100


def test_visible_ratio_bounds():
    points = np.array([[0, 0, 3], [0, 0, 1]])
    ratio = visible_ratio(points, z_threshold=2.0)
    assert 0.0 <= ratio <= 1.0
