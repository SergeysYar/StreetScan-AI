"""PointNet++ integration contract placeholder."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class PointNetInterface:
    """Future model wrapper interface."""
    model_path: str | None = None

    def predict(self, points: np.ndarray) -> np.ndarray:
        """Return placeholder semantic classes until model integration is added."""
        return np.zeros(len(points), dtype=int)
