"""Heatmap rendering utilities for density and occupancy data."""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def render_density_heatmap_from_points(points: np.ndarray, output_path: Path, resolution: float, dpi: int) -> None:
    """Render density heatmap directly from point array."""
    if len(points) == 0:
        raise ValueError("Cannot render heatmap for empty points")
    if resolution <= 0:
        raise ValueError("resolution must be > 0")
    x, y = points[:, 0], points[:, 1]
    xb = max(1, int(np.ceil((x.max() - x.min()) / resolution)))
    yb = max(1, int(np.ceil((y.max() - y.min()) / resolution)))
    h, _, _ = np.histogram2d(x, y, bins=[xb, yb])

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 6))
    im = ax.imshow(h.T, origin="lower", cmap="magma")
    ax.set_title("Density Heatmap")
    ax.set_xlabel("X cells")
    ax.set_ylabel("Y cells")
    fig.colorbar(im, ax=ax, label="point_count")
    fig.tight_layout()
    fig.savefig(output_path, dpi=dpi)
    plt.close(fig)


def render_density_heatmap_from_csv(csv_path: Path, output_path: Path, dpi: int) -> None:
    """Render density heatmap from flattened density CSV."""
    df = pd.read_csv(csv_path)
    req = {"cell_x", "cell_y", "density"}
    if not req.issubset(df.columns):
        raise ValueError(f"Density CSV missing required columns: {sorted(req)}")
    w = int(df["cell_x"].max()) + 1
    h = int(df["cell_y"].max()) + 1
    grid = np.zeros((w, h), dtype=float)
    for r in df.itertuples(index=False):
        grid[int(r.cell_x), int(r.cell_y)] = float(r.density)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 6))
    im = ax.imshow(grid.T, origin="lower", cmap="magma")
    ax.set_title("Density Heatmap (CSV)")
    ax.set_xlabel("X cells")
    ax.set_ylabel("Y cells")
    fig.colorbar(im, ax=ax, label="density")
    fig.tight_layout()
    fig.savefig(output_path, dpi=dpi)
    plt.close(fig)


def render_occupancy_map_from_csv(csv_path: Path, output_path: Path, dpi: int) -> None:
    """Render occupancy grid map from CSV."""
    df = pd.read_csv(csv_path)
    req = {"cell_x", "cell_y", "occupied"}
    if not req.issubset(df.columns):
        raise ValueError(f"Occupancy CSV missing required columns: {sorted(req)}")
    w = int(df["cell_x"].max()) + 1
    h = int(df["cell_y"].max()) + 1
    grid = np.zeros((w, h), dtype=float)
    for r in df.itertuples(index=False):
        grid[int(r.cell_x), int(r.cell_y)] = float(r.occupied)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 6))
    im = ax.imshow(grid.T, origin="lower", cmap="Greys")
    ax.set_title("Occupancy Map")
    ax.set_xlabel("X cells")
    ax.set_ylabel("Y cells")
    fig.colorbar(im, ax=ax, label="occupied")
    fig.tight_layout()
    fig.savefig(output_path, dpi=dpi)
    plt.close(fig)
