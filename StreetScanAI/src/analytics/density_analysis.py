"""Density analysis and heatmap preparation."""
from __future__ import annotations

import numpy as np


def density_histogram(points: np.ndarray, resolution: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Compute 2D density histogram on XY plane."""
    x = points[:, 0]
    y = points[:, 1]
    bins_x = max(2, int((x.max() - x.min()) / resolution) + 1)
    bins_y = max(2, int((y.max() - y.min()) / resolution) + 1)
    hist, xedges, yedges = np.histogram2d(x, y, bins=[bins_x, bins_y])
    return hist, xedges, yedges
