"""Velocity estimation utilities for tracked trajectories."""
from __future__ import annotations

import math

import numpy as np
import pandas as pd


def compute_speed(vx: float, vy: float, vz: float) -> float:
    """Compute scalar speed from velocity components."""
    return float(math.sqrt(vx * vx + vy * vy + vz * vz))


def estimate_velocity_from_points(points: pd.DataFrame, fps: float) -> pd.DataFrame:
    """Estimate per-point velocity for each track."""
    if fps <= 0:
        raise ValueError("fps must be > 0")
    df = points.copy().sort_values(["track_id", "frame_id"]).reset_index(drop=True)
    df[["vx", "vy", "vz", "speed"]] = np.nan

    for track_id, grp in df.groupby("track_id", sort=False):
        idx = grp.index.to_numpy()
        x = grp["x"].to_numpy(dtype=float)
        y = grp["y"].to_numpy(dtype=float)
        z = grp["z"].to_numpy(dtype=float)

        if "timestamp" in grp.columns and grp["timestamp"].notna().all():
            t = grp["timestamp"].to_numpy(dtype=float)
            dt = np.diff(t, prepend=t[0])
            dt[0] = 1.0 / fps
            dt[dt <= 0] = 1.0 / fps
        else:
            dt = np.full(len(grp), 1.0 / fps, dtype=float)

        vx = np.diff(x, prepend=x[0]) / dt
        vy = np.diff(y, prepend=y[0]) / dt
        vz = np.diff(z, prepend=z[0]) / dt
        speed = np.sqrt(vx * vx + vy * vy + vz * vz)

        df.loc[idx, "vx"] = vx
        df.loc[idx, "vy"] = vy
        df.loc[idx, "vz"] = vz
        df.loc[idx, "speed"] = speed
    return df


def summarize_velocity(track_points: pd.DataFrame) -> pd.DataFrame:
    """Summarize velocity statistics per track."""
    if "speed" not in track_points.columns:
        return pd.DataFrame(columns=["track_id", "mean_speed", "max_speed"]) 
    grp = track_points.groupby("track_id", as_index=False).agg(mean_speed=("speed", "mean"), max_speed=("speed", "max"))
    return grp
