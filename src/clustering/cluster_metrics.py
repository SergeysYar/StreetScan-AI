"""Clustering metric utilities."""
from __future__ import annotations

import numpy as np


def cluster_summary(labels: np.ndarray) -> dict[str, float]:
    """Basic clustering summary metrics."""
    valid = labels[labels >= 0]
    unique = set(valid.tolist())
    return {
        "cluster_count": float(len(unique)),
        "noise_points": float((labels < 0).sum()),
        "mean_cluster_size": float(len(valid) / len(unique)) if unique else 0.0,
    }
