"""Trajectory rendering utilities for 2D/3D plots and overlays."""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import open3d as o3d
import pandas as pd

from src.visualization.pointcloud_viewer import ViewerConfig, load_cloud, render_pointcloud


def load_trajectories(path: Path) -> pd.DataFrame:
    """Load tracked trajectory CSV."""
    if not path.exists():
        raise FileNotFoundError(f"Trajectory CSV not found: {path}")
    df = pd.read_csv(path)
    required = {"track_id", "frame_id"}
    if not required.issubset(df.columns):
        raise ValueError(f"Trajectory CSV missing required columns: {sorted(required)}")
    for col in ["x", "y", "z"]:
        if col not in df.columns and f"smoothed_{col}" not in df.columns:
            raise ValueError(f"Trajectory CSV missing coordinate column: {col} or smoothed_{col}")
    return df


def _coord_cols(df: pd.DataFrame) -> tuple[str, str, str]:
    x = "smoothed_x" if "smoothed_x" in df.columns else "x"
    y = "smoothed_y" if "smoothed_y" in df.columns else "y"
    z = "smoothed_z" if "smoothed_z" in df.columns else "z"
    return x, y, z


def plot_trajectories_2d(df: pd.DataFrame, output_path: Path, dpi: int) -> None:
    """Plot XY trajectories."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    xcol, ycol, _ = _coord_cols(df)
    fig, ax = plt.subplots(figsize=(9, 6))
    grouped = list(df.groupby("track_id", sort=False))
    for tid, grp in grouped:
        ax.plot(grp[xcol], grp[ycol], label=f"T{tid}")
        if len(grp) > 3:
            ax.annotate("", xy=(grp[xcol].iloc[-1], grp[ycol].iloc[-1]), xytext=(grp[xcol].iloc[-2], grp[ycol].iloc[-2]), arrowprops=dict(arrowstyle="->", lw=1))
    ax.set_title("Trajectories XY")
    ax.set_xlabel("X (m)")
    ax.set_ylabel("Y (m)")
    if len(grouped) <= 20:
        ax.legend(loc="best", fontsize=8)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(output_path, dpi=dpi)
    plt.close(fig)


def plot_trajectories_3d(df: pd.DataFrame, output_path: Path, dpi: int) -> None:
    """Plot 3D trajectories with matplotlib 3D axes."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    xcol, ycol, zcol = _coord_cols(df)
    fig = plt.figure(figsize=(9, 6))
    ax = fig.add_subplot(111, projection="3d")
    grouped = list(df.groupby("track_id", sort=False))
    for tid, grp in grouped:
        ax.plot(grp[xcol], grp[ycol], grp[zcol], label=f"T{tid}")
    ax.set_title("Trajectories 3D")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")
    if len(grouped) <= 12:
        ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    fig.savefig(output_path, dpi=dpi)
    plt.close(fig)


def render_trajectory_overlay(cloud_path: Path, trajectory_path: Path, output_path: Path, config: ViewerConfig) -> None:
    """Render cloud with overlaid trajectory points."""
    cloud = load_cloud(cloud_path)
    df = load_trajectories(trajectory_path)
    xcol, ycol, zcol = _coord_cols(df)
    traj_pts = df[[xcol, ycol, zcol]].to_numpy(dtype=float)

    overlay = o3d.geometry.PointCloud(cloud)
    base_pts = np.asarray(cloud.points)
    base_cols = np.asarray(cloud.colors) if cloud.has_colors() else np.tile(np.array([[0.7, 0.7, 0.7]]), (len(base_pts), 1))

    rng = np.random.default_rng(42)
    tids = df["track_id"].to_numpy(dtype=int)
    uniq = sorted(set(tids.tolist()))
    palette = {tid: rng.random(3) for tid in uniq}
    traj_cols = np.array([palette[int(t)] for t in tids], dtype=float)

    all_pts = np.vstack([base_pts, traj_pts])
    all_cols = np.vstack([base_cols, traj_cols])
    overlay.points = o3d.utility.Vector3dVector(all_pts)
    overlay.colors = o3d.utility.Vector3dVector(all_cols)
    render_pointcloud(overlay, output_path, config)
