"""Heuristic semantic segmentation placeholder."""
from __future__ import annotations

import numpy as np


def segment_points(points: np.ndarray) -> np.ndarray:
    """Assign simple semantic labels from geometric heuristics."""
    labels = np.zeros(len(points), dtype=int)
    z = points[:, 2]
    labels[z > 2.5] = 7
    labels[(z > 0.5) & (z <= 2.5)] = 2
    labels[(z > 0.1) & (z <= 0.5)] = 1
    labels[(z <= 0.1)] = 0
    return labels
