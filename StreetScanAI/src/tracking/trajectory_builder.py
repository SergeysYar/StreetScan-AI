"""Trajectory building from frame-wise centroids."""
from __future__ import annotations

import pandas as pd


def build_trajectories(frame_cluster_df: pd.DataFrame) -> pd.DataFrame:
    """Build trajectories assuming persistent cluster IDs between frames."""
    trajectory = frame_cluster_df.copy()
    trajectory["object_id"] = trajectory["cluster_id"]
    return trajectory.sort_values(["object_id", "frame"])
