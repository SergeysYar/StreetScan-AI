"""Occupancy grid generation for XY projected LiDAR points."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


@dataclass
class OccupancyConfig:
    """Configuration for occupancy map construction."""

    grid_resolution: float = 0.5
    occupancy_threshold: int = 1


@dataclass
class OccupancyGridResult:
    """Occupancy grid data and metrics."""

    grid_counts: np.ndarray
    occupied_mask: np.ndarray
    x_edges: np.ndarray
    y_edges: np.ndarray
    occupancy_ratio: float


def build_occupancy_grid(points: np.ndarray, config: OccupancyConfig) -> OccupancyGridResult:
    """Build occupancy grid from XY projections."""
    if config.grid_resolution <= 0:
        raise ValueError("grid_resolution must be > 0")
    if config.occupancy_threshold <= 0:
        raise ValueError("occupancy_threshold must be > 0")
    if len(points) == 0:
        raise ValueError("Cannot build occupancy grid for empty point array")

    x = points[:, 0]
    y = points[:, 1]
    x_min, x_max = float(x.min()), float(x.max())
    y_min, y_max = float(y.min()), float(y.max())
    x_bins = max(1, int(np.ceil((x_max - x_min) / config.grid_resolution)))
    y_bins = max(1, int(np.ceil((y_max - y_min) / config.grid_resolution)))
    x_edges = np.linspace(x_min, x_max if x_max > x_min else x_min + config.grid_resolution, x_bins + 1)
    y_edges = np.linspace(y_min, y_max if y_max > y_min else y_min + config.grid_resolution, y_bins + 1)

    counts, _, _ = np.histogram2d(x, y, bins=[x_edges, y_edges])
    occupied = counts >= config.occupancy_threshold
    ratio = float(occupied.sum() / occupied.size)

    return OccupancyGridResult(
        grid_counts=counts,
        occupied_mask=occupied.astype(int),
        x_edges=x_edges,
        y_edges=y_edges,
        occupancy_ratio=ratio,
    )


def save_occupancy_csv(result: OccupancyGridResult, output_path: Path) -> None:
    """Save occupancy cells to CSV."""
    rows = []
    for i in range(result.grid_counts.shape[0]):
        for j in range(result.grid_counts.shape[1]):
            rows.append(
                {
                    "cell_x": i,
                    "cell_y": j,
                    "x_min": float(result.x_edges[i]),
                    "x_max": float(result.x_edges[i + 1]),
                    "y_min": float(result.y_edges[j]),
                    "y_max": float(result.y_edges[j + 1]),
                    "point_count": int(result.grid_counts[i, j]),
                    "occupied": int(result.occupied_mask[i, j]),
                }
            )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(output_path, index=False)


def plot_occupancy_map(result: OccupancyGridResult, output_path: Path, dpi: int = 150) -> None:
    """Render occupancy map image."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 6))
    im = ax.imshow(result.occupied_mask.T, origin="lower", cmap="Greys", aspect="auto")
    ax.set_title("Occupancy Map")
    ax.set_xlabel("Grid X")
    ax.set_ylabel("Grid Y")
    fig.colorbar(im, ax=ax, label="Occupied")
    fig.tight_layout()
    fig.savefig(output_path, dpi=dpi)
    plt.close(fig)


def compute_occupancy_grid(points: np.ndarray, resolution: float) -> np.ndarray:
    """Backward-compatible occupancy helper."""
    result = build_occupancy_grid(points, OccupancyConfig(grid_resolution=resolution, occupancy_threshold=1))
    return result.occupied_mask
