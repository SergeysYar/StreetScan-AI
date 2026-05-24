"""Visibility estimation."""
from __future__ import annotations

import numpy as np


def visible_ratio(points: np.ndarray, z_threshold: float) -> float:
    """Estimate visible-point ratio using Z threshold."""
    if len(points) == 0:
        return 0.0
    return float((points[:, 2] > z_threshold).sum() / len(points))
