"""PointNet++ integration placeholder for semantic segmentation."""
from __future__ import annotations

from pathlib import Path

import numpy as np


class PointNetSegmenter:
    """Integration contract for future PointNet++ inference."""

    def __init__(self, weights_path: Path | None, device: str = "cpu") -> None:
        self.weights_path = weights_path
        self.device = device
        self._loaded = False

    def is_available(self) -> bool:
        """Return True when weights path exists and model can be loaded."""
        return self.weights_path is not None and self.weights_path.exists()

    def load_model(self) -> None:
        """Load trained model weights (placeholder contract)."""
        if self.weights_path is None:
            raise RuntimeError("PointNet++ weights_path is not provided.")
        if not self.weights_path.exists():
            raise FileNotFoundError(f"PointNet++ weights not found: {self.weights_path}")
        # Future integration point:
        # 1) instantiate PointNet++ architecture
        # 2) load checkpoint to the selected device
        # 3) switch model to eval mode
        self._loaded = True

    def predict(self, points: np.ndarray) -> np.ndarray:
        """Run model inference (not implemented in placeholder)."""
        if self.weights_path is None:
            raise RuntimeError("PointNet++ inference unavailable: weights_path is None.")
        if not self.weights_path.exists():
            raise FileNotFoundError(f"PointNet++ weights not found: {self.weights_path}")
        if not self._loaded:
            self.load_model()
        raise RuntimeError(
            "PointNet++ inference placeholder is not implemented yet. "
            "Insert real model forward pass in PointNetSegmenter.predict()."
        )
