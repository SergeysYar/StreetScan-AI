"""Spatial descriptive statistics."""
from __future__ import annotations

import numpy as np


def spatial_stats(points: np.ndarray) -> dict[str, float]:
    """Compute descriptive stats over XYZ coordinates."""
    return {
        "mean_x": float(points[:, 0].mean()),
        "mean_y": float(points[:, 1].mean()),
        "mean_z": float(points[:, 2].mean()),
        "std_x": float(points[:, 0].std()),
        "std_y": float(points[:, 1].std()),
        "std_z": float(points[:, 2].std()),
        "point_count": float(len(points)),
    }
