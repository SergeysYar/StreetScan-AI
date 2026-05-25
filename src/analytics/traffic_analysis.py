"""Traffic density analysis from semantic and cluster sources."""
from __future__ import annotations

from pathlib import Path

import pandas as pd


def analyze_traffic(
    semantic_labels: pd.DataFrame | None,
    cluster_stats: pd.DataFrame | None,
    scene_area: float,
    vehicle_label_names: list[str],
) -> pd.DataFrame:
    """Compute traffic metrics using available sources."""
    rows: list[dict[str, object]] = []
    area = max(scene_area, 1e-9)

    if semantic_labels is not None and "label_name" in semantic_labels.columns:
        veh_points = int(semantic_labels[semantic_labels["label_name"].isin(vehicle_label_names)].shape[0])
        rows.append({"metric": "vehicle_point_count", "value": veh_points, "unit": "points", "source": "semantic", "notes": "measured"})
        rows.append(
            {
                "metric": "estimated_vehicle_density",
                "value": float(veh_points / area),
                "unit": "points_per_m2",
                "source": "semantic",
                "notes": "estimated",
            }
        )

    if cluster_stats is not None and not cluster_stats.empty:
        work = cluster_stats.copy()
        for col in ["extent_x", "extent_y", "extent_z"]:
            if col not in work.columns:
                work[col] = 0.0
        compact = (work["extent_x"] < 5.0) & (work["extent_y"] < 3.0) & (work["extent_z"].between(1.0, 3.5))
        veh_clusters = int(work[compact].shape[0])
        rows.append({"metric": "vehicle_cluster_count", "value": veh_clusters, "unit": "clusters", "source": "cluster_stats", "notes": "heuristic"})
        rows.append(
            {
                "metric": "vehicle_area_share",
                "value": float(work[compact]["bbox_volume"].sum() / max(work["bbox_volume"].sum(), 1e-9)) if "bbox_volume" in work else 0.0,
                "unit": "ratio",
                "source": "cluster_stats",
                "notes": "heuristic",
            }
        )

    if not rows:
        rows.append({"metric": "traffic_available", "value": 0, "unit": "flag", "source": "none", "notes": "unavailable"})
    return pd.DataFrame(rows)


def save_traffic_summary(df: pd.DataFrame, output_path: Path) -> None:
    """Save traffic summary CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
