"""Velocity estimation for trajectories."""
from __future__ import annotations

import numpy as np
import pandas as pd


def estimate_velocity(tracks: pd.DataFrame, dt: float = 0.1) -> pd.DataFrame:
    """Estimate speed per object and frame."""
    tracks = tracks.copy()
    tracks[["vx", "vy", "vz", "speed"]] = 0.0
    for obj_id, group in tracks.groupby("object_id"):
        idx = group.index.tolist()
        diffs = np.diff(group[["centroid_x", "centroid_y", "centroid_z"]].values, axis=0, prepend=group[["centroid_x", "centroid_y", "centroid_z"]].values[:1])
        vel = diffs / dt
        tracks.loc[idx, ["vx", "vy", "vz"]] = vel
        tracks.loc[idx, "speed"] = np.linalg.norm(vel, axis=1)
    return tracks
