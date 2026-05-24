"""Geometry utilities for point clouds."""
from __future__ import annotations

import numpy as np


def axis_aligned_bbox(points: np.ndarray) -> dict[str, np.ndarray]:
    """Compute axis-aligned bounding box for N x 3 points."""
    min_xyz = points.min(axis=0)
    max_xyz = points.max(axis=0)
    return {"min": min_xyz, "max": max_xyz, "size": max_xyz - min_xyz}


def center_points(points: np.ndarray) -> np.ndarray:
    """Center points around origin."""
    return points - points.mean(axis=0)


def normalize_points(points: np.ndarray) -> np.ndarray:
    """Scale points to unit sphere."""
    centered = center_points(points)
    norm = np.linalg.norm(centered, axis=1).max()
    return centered if norm == 0 else centered / norm
