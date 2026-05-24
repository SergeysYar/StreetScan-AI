"""Traffic density statistics."""
from __future__ import annotations

import pandas as pd


def traffic_density_from_tracks(tracks: pd.DataFrame) -> pd.DataFrame:
    """Compute per-object average speed and frame occupancy."""
    summary = tracks.groupby("object_id").agg(avg_speed=("speed", "mean"), frames=("frame", "nunique")).reset_index()
    return summary
