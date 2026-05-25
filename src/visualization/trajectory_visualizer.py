"""Trajectory visualization facade."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.tracking.track_visualization import plot_trajectories


def render_trajectories(tracks: pd.DataFrame, out_path: Path) -> None:
    """Render trajectory figure."""
    plot_trajectories(tracks, out_path)
