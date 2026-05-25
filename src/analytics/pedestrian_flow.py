"""Pedestrian flow and concentration analytics."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def analyze_pedestrian_flow(
    semantic_labels: pd.DataFrame | None,
    trajectories: pd.DataFrame | None,
    scene_area: float,
    pedestrian_label_names: list[str],
) -> pd.DataFrame:
    """Estimate pedestrian concentration and optional flow metrics."""
    rows: list[dict[str, object]] = []
    area = max(scene_area, 1e-9)

    ped_points = 0
    if semantic_labels is not None and "label_name" in semantic_labels.columns:
        ped_points = int(semantic_labels[semantic_labels["label_name"].isin(pedestrian_label_names)].shape[0])
        rows.append({"metric": "pedestrian_point_count", "value": ped_points, "unit": "points", "source": "semantic", "notes": "measured"})
        rows.append({"metric": "pedestrian_density", "value": float(ped_points / area), "unit": "points_per_m2", "source": "semantic", "notes": "estimated"})

    if trajectories is not None and not trajectories.empty:
        required = {"track_id", "x", "y"}
        if required.issubset(trajectories.columns):
            flow_count = int(trajectories["track_id"].nunique())
            rows.append({"metric": "flow_available", "value": 1, "unit": "flag", "source": "trajectory", "notes": "measured"})
            rows.append({"metric": "pedestrian_cluster_count", "value": flow_count, "unit": "tracks", "source": "trajectory", "notes": "estimated"})

            if "velocity" in trajectories.columns:
                rows.append(
                    {
                        "metric": "average_speed",
                        "value": float(pd.to_numeric(trajectories["velocity"], errors="coerce").dropna().mean()) if trajectories["velocity"].notna().any() else 0.0,
                        "unit": "m_s",
                        "source": "trajectory",
                        "notes": "measured",
                    }
                )

            dx = trajectories.groupby("track_id")["x"].apply(lambda s: float(s.iloc[-1] - s.iloc[0]))
            dy = trajectories.groupby("track_id")["y"].apply(lambda s: float(s.iloc[-1] - s.iloc[0]))
            angles = np.degrees(np.arctan2(dy.values, dx.values))
            dominant = float(np.angle(np.mean(np.exp(1j * np.radians(angles))), deg=True)) if len(angles) > 0 else 0.0
            rows.append({"metric": "dominant_direction_deg", "value": dominant, "unit": "deg", "source": "trajectory", "notes": "estimated"})
        else:
            rows.append({"metric": "flow_available", "value": 0, "unit": "flag", "source": "trajectory", "notes": "unavailable_columns"})
    else:
        rows.append({"metric": "flow_available", "value": 0, "unit": "flag", "source": "none", "notes": "unavailable"})

    if not rows:
        rows.append({"metric": "pedestrian_available", "value": 0, "unit": "flag", "source": "none", "notes": "unavailable"})
    return pd.DataFrame(rows)


def save_pedestrian_flow(df: pd.DataFrame, output_path: Path) -> None:
    """Save pedestrian flow CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
