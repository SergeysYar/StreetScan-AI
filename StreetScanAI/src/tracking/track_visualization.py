"""Trajectory plotting utilities."""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def plot_trajectories(tracks: pd.DataFrame, out_path: Path) -> None:
    """Render trajectory plot for all objects."""
    fig, ax = plt.subplots(figsize=(8, 6))
    for object_id, group in tracks.groupby("object_id"):
        ax.plot(group["centroid_x"], group["centroid_y"], label=f"obj {object_id}")
    ax.set_title("Object Trajectories")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.legend(loc="best", fontsize=8)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
