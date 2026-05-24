"""Semantic color mapping."""
from __future__ import annotations

import numpy as np

COLOR_MAP = {
    0: (0.3, 0.3, 0.3),
    1: (0.7, 0.7, 0.7),
    2: (1.0, 0.2, 0.2),
    3: (1.0, 0.8, 0.2),
    4: (0.2, 0.8, 0.2),
    5: (0.8, 0.8, 0.1),
    6: (1.0, 0.5, 0.0),
    7: (0.2, 0.4, 1.0),
}


def labels_to_colors(labels: np.ndarray) -> np.ndarray:
    """Convert semantic labels to RGB colors."""
    return np.array([COLOR_MAP.get(int(label), (1.0, 1.0, 1.0)) for label in labels], dtype=float)
