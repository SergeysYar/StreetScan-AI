"""Kalman tracking placeholder."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class KalmanTracker:
    """Minimal tracker placeholder for extensibility."""
    object_id: int

    def update(self, measurement: np.ndarray) -> np.ndarray:
        """Return the measurement as state placeholder."""
        return measurement
