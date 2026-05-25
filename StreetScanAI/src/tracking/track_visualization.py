"""Trajectory visualization utilities."""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import open3d as o3d
import pandas as pd


def plot_trajectories_xy(track_points: pd.DataFrame, output_path: Path, dpi: int = 150) -> None:
    """Plot XY trajectories for all tracks."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(9, 6))
    grouped = list(track_points.groupby("track_id", sort=False))
    for track_id, grp in grouped:
        x_col = "smoothed_x" if "smoothed_x" in grp.columns else "x"
        y_col = "smoothed_y" if "smoothed_y" in grp.columns else "y"
        ax.plot(grp[x_col], grp[y_col], label=f"T{track_id}")
    ax.set_title("Tracked Trajectories (XY)")
    ax.set_xlabel("X (m)")
    ax.set_ylabel("Y (m)")
    if len(grouped) <= 20:
        ax.legend(loc="best", fontsize=8)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(output_path, dpi=dpi)
    plt.close(fig)


def plot_velocity_profiles(track_points: pd.DataFrame, output_path: Path, dpi: int = 150) -> None:
    """Plot speed over frame index per track."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(9, 6))
    grouped = list(track_points.groupby("track_id", sort=False))
    for track_id, grp in grouped:
        speed = grp["speed"] if "speed" in grp.columns else np.zeros(len(grp))
        ax.plot(grp["frame_id"], speed, label=f"T{track_id}")
    ax.set_title("Velocity Profiles")
    ax.set_xlabel("Frame ID")
    ax.set_ylabel("Speed (m/s)")
    if len(grouped) <= 20:
        ax.legend(loc="best", fontsize=8)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(output_path, dpi=dpi)
    plt.close(fig)


def create_trajectory_overlay_cloud(track_points: pd.DataFrame, output_path: Path) -> None:
    """Create trajectory overlay point cloud colored by track_id."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pts = track_points[["x", "y", "z"]].to_numpy(dtype=float)
    ids = track_points["track_id"].to_numpy(dtype=int)
    if len(pts) == 0:
        raise ValueError("No trajectory points available for overlay export.")
    rng = np.random.default_rng(42)
    unique_ids = sorted(set(ids.tolist()))
    palette = {tid: rng.random(3) for tid in unique_ids}
    cols = np.array([palette[int(tid)] for tid in ids], dtype=float)

    cloud = o3d.geometry.PointCloud()
    cloud.points = o3d.utility.Vector3dVector(pts)
    cloud.colors = o3d.utility.Vector3dVector(cols)
    ok = o3d.io.write_point_cloud(str(output_path), cloud)
    if not ok:
        raise RuntimeError(f"Failed to write overlay cloud: {output_path}")
