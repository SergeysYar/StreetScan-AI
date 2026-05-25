"""Trajectory smoothing utilities."""
from __future__ import annotations

import pandas as pd


def moving_average_smoothing(track_df: pd.DataFrame, window: int) -> pd.DataFrame:
    """Apply moving average smoothing for one track."""
    if window <= 1 or len(track_df) <= 1:
        out = track_df.copy()
        out["smoothed_x"] = out["x"]
        out["smoothed_y"] = out["y"]
        out["smoothed_z"] = out["z"]
        return out

    out = track_df.copy().sort_values("frame_id")
    out["smoothed_x"] = out["x"].rolling(window=window, min_periods=1, center=True).mean()
    out["smoothed_y"] = out["y"].rolling(window=window, min_periods=1, center=True).mean()
    out["smoothed_z"] = out["z"].rolling(window=window, min_periods=1, center=True).mean()
    return out


def smooth_all_tracks(track_points: pd.DataFrame, window: int) -> pd.DataFrame:
    """Apply smoothing independently to each track."""
    chunks = []
    for _, grp in track_points.groupby("track_id", sort=False):
        chunks.append(moving_average_smoothing(grp, window))
    if not chunks:
        out = track_points.copy()
        out["smoothed_x"] = out.get("x")
        out["smoothed_y"] = out.get("y")
        out["smoothed_z"] = out.get("z")
        return out
    return pd.concat(chunks, ignore_index=True)
