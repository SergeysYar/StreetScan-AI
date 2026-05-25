"""Global spatial statistics for urban LiDAR scenes."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def compute_spatial_statistics(
    points: np.ndarray,
    semantic_labels: pd.DataFrame | None = None,
    cluster_stats: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Compute global scene statistics and optional semantic/cluster metrics."""
    if len(points) == 0:
        raise ValueError("Cannot compute statistics for empty point array")

    min_xyz = points.min(axis=0)
    max_xyz = points.max(axis=0)
    ext = max_xyz - min_xyz
    area = float(max(ext[0] * ext[1], 0.0))
    volume = float(max(ext[0] * ext[1] * ext[2], 0.0))
    density = float(len(points) / area) if area > 0 else 0.0

    rows: list[dict[str, object]] = [
        {"metric": "total_point_count", "value": int(len(points)), "unit": "points", "notes": "measured"},
        {"metric": "bbox_min", "value": str([float(v) for v in min_xyz]), "unit": "xyz", "notes": "measured"},
        {"metric": "bbox_max", "value": str([float(v) for v in max_xyz]), "unit": "xyz", "notes": "measured"},
        {"metric": "scene_extent", "value": str([float(v) for v in ext]), "unit": "m", "notes": "measured"},
        {"metric": "scene_area_estimate", "value": area, "unit": "m2", "notes": "estimated"},
        {"metric": "scene_volume_estimate", "value": volume, "unit": "m3", "notes": "estimated"},
        {"metric": "centroid", "value": str([float(v) for v in points.mean(axis=0)]), "unit": "xyz", "notes": "measured"},
        {"metric": "height_range", "value": float(ext[2]), "unit": "m", "notes": "measured"},
        {"metric": "mean_height", "value": float(points[:, 2].mean()), "unit": "m", "notes": "measured"},
        {"metric": "median_height", "value": float(np.median(points[:, 2])), "unit": "m", "notes": "measured"},
        {"metric": "point_density", "value": density, "unit": "points_per_m2", "notes": "estimated"},
    ]

    if semantic_labels is not None and "label_name" in semantic_labels.columns:
        counts = semantic_labels["label_name"].value_counts().to_dict()
        rows.append({"metric": "semantic_class_count", "value": int(len(counts)), "unit": "classes", "notes": "measured"})
        rows.append({"metric": "semantic_distribution", "value": str({k: int(v) for k, v in counts.items()}), "unit": "dict", "notes": "measured"})

    if cluster_stats is not None and not cluster_stats.empty:
        rows.append({"metric": "cluster_count", "value": int(cluster_stats.shape[0]), "unit": "clusters", "notes": "measured"})

    return pd.DataFrame(rows)


def save_spatial_statistics(stats_df: pd.DataFrame, output_path: Path) -> None:
    """Save spatial statistics CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    stats_df.to_csv(output_path, index=False)


def spatial_stats(points: np.ndarray) -> dict[str, float]:
    """Backward-compatible compact statistics helper."""
    return {
        "mean_x": float(points[:, 0].mean()),
        "mean_y": float(points[:, 1].mean()),
        "mean_z": float(points[:, 2].mean()),
        "std_x": float(points[:, 0].std()),
        "std_y": float(points[:, 1].std()),
        "std_z": float(points[:, 2].std()),
        "point_count": float(len(points)),
    }
