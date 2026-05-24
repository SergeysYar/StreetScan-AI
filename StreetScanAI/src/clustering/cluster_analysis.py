"""Cluster analysis and bounding boxes."""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.utils.geometry_utils import axis_aligned_bbox


def extract_cluster_stats(points: np.ndarray, labels: np.ndarray) -> pd.DataFrame:
    """Compute per-cluster statistics."""
    rows = []
    for cluster_id in sorted(set(labels.tolist()) - {-1}):
        subset = points[labels == cluster_id]
        bbox = axis_aligned_bbox(subset)
        rows.append({
            "cluster_id": int(cluster_id),
            "num_points": int(len(subset)),
            "centroid_x": float(subset[:, 0].mean()),
            "centroid_y": float(subset[:, 1].mean()),
            "centroid_z": float(subset[:, 2].mean()),
            "bbox_dx": float(bbox["size"][0]),
            "bbox_dy": float(bbox["size"][1]),
            "bbox_dz": float(bbox["size"][2]),
        })
    return pd.DataFrame(rows)
