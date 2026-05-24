"""Occupancy grid generation."""
from __future__ import annotations

import numpy as np


def compute_occupancy_grid(points: np.ndarray, resolution: float) -> np.ndarray:
    """Binary occupancy from density histogram."""
    hist, _, _ = np.histogram2d(points[:, 0], points[:, 1], bins=max(2, int(20 / resolution)))
    return (hist > 0).astype(int)
