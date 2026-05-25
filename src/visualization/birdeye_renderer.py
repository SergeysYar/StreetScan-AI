"""Bird-eye view renderers for LiDAR point clouds."""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.visualization.pointcloud_viewer import load_cloud


def create_bird_eye_projection(points: np.ndarray, resolution: float) -> np.ndarray:
    """Project XYZ points onto XY density grid."""
    if resolution <= 0:
        raise ValueError("resolution must be > 0")
    if len(points) == 0:
        raise ValueError("empty points")
    x, y = points[:, 0], points[:, 1]
    xb = max(1, int(np.ceil((x.max() - x.min()) / resolution)))
    yb = max(1, int(np.ceil((y.max() - y.min()) / resolution)))
    h, _, _ = np.histogram2d(x, y, bins=[xb, yb])
    return h.T


def render_bird_eye_view(cloud_path: Path, output_path: Path, resolution: float, dpi: int) -> None:
    """Render point density bird-eye image from cloud."""
    cloud = load_cloud(cloud_path)
    pts = np.asarray(cloud.points)
    grid = create_bird_eye_projection(pts, resolution)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 6))
    im = ax.imshow(grid, origin="lower", cmap="viridis")
    ax.set_title("Bird-Eye Density View")
    ax.set_xlabel("X cells")
    ax.set_ylabel("Y cells")
    fig.colorbar(im, ax=ax, label="point_count")
    fig.tight_layout()
    fig.savefig(output_path, dpi=dpi)
    plt.close(fig)


def render_semantic_bird_eye(points: np.ndarray, labels: np.ndarray, output_path: Path, resolution: float, dpi: int) -> None:
    """Render semantic bird-eye map using dominant class per cell."""
    if len(points) != len(labels):
        raise ValueError("labels length mismatch")
    x, y = points[:, 0], points[:, 1]
    x_min, x_max = x.min(), x.max()
    y_min, y_max = y.min(), y.max()
    xb = max(1, int(np.ceil((x_max - x_min) / resolution)))
    yb = max(1, int(np.ceil((y_max - y_min) / resolution)))
    xi = np.clip(((x - x_min) / max(resolution, 1e-9)).astype(int), 0, xb - 1)
    yi = np.clip(((y - y_min) / max(resolution, 1e-9)).astype(int), 0, yb - 1)

    cell = {}
    for i in range(len(points)):
        key = (yi[i], xi[i])
        cell.setdefault(key, []).append(int(labels[i]))

    grid = np.full((yb, xb), -1, dtype=int)
    for (yy, xx), lab in cell.items():
        vals, cnt = np.unique(np.array(lab, dtype=int), return_counts=True)
        grid[yy, xx] = int(vals[np.argmax(cnt)])

    cmap = plt.get_cmap("tab20")
    vis = np.zeros((yb, xb, 3), dtype=float)
    for yy in range(yb):
        for xx in range(xb):
            lid = grid[yy, xx]
            if lid < 0:
                vis[yy, xx] = (1.0, 1.0, 1.0)
            else:
                vis[yy, xx] = cmap(lid % 20)[:3]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.imshow(vis, origin="lower")
    ax.set_title("Semantic Bird-Eye View")
    ax.set_xlabel("X cells")
    ax.set_ylabel("Y cells")
    fig.tight_layout()
    fig.savefig(output_path, dpi=dpi)
    plt.close(fig)
