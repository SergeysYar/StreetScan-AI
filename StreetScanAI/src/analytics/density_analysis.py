"""Point density analysis for urban LiDAR scenes."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


@dataclass
class DensityConfig:
    """Configuration for density grid computation."""

    grid_resolution: float = 0.5
    density_normalization: bool = True
    plot_dpi: int = 150


@dataclass
class DensityResult:
    """Density grid and aggregate metrics."""

    grid: np.ndarray
    x_edges: np.ndarray
    y_edges: np.ndarray
    resolution: float
    max_density: float
    mean_density: float
    occupied_cells: int
    total_cells: int


def compute_density_grid(points: np.ndarray, config: DensityConfig) -> DensityResult:
    """Project points onto XY and compute density grid."""
    if config.grid_resolution <= 0:
        raise ValueError("grid_resolution must be > 0")
    if len(points) == 0:
        raise ValueError("Cannot compute density grid for empty point array")

    x = points[:, 0]
    y = points[:, 1]
    x_min, x_max = float(x.min()), float(x.max())
    y_min, y_max = float(y.min()), float(y.max())
    x_bins = max(1, int(np.ceil((x_max - x_min) / config.grid_resolution)))
    y_bins = max(1, int(np.ceil((y_max - y_min) / config.grid_resolution)))
    x_edges = np.linspace(x_min, x_max if x_max > x_min else x_min + config.grid_resolution, x_bins + 1)
    y_edges = np.linspace(y_min, y_max if y_max > y_min else y_min + config.grid_resolution, y_bins + 1)

    counts, _, _ = np.histogram2d(x, y, bins=[x_edges, y_edges])
    cell_area = config.grid_resolution * config.grid_resolution
    density = counts / cell_area
    if config.density_normalization and density.max() > 0:
        density = density / density.max()

    return DensityResult(
        grid=density,
        x_edges=x_edges,
        y_edges=y_edges,
        resolution=config.grid_resolution,
        max_density=float(density.max()),
        mean_density=float(density.mean()),
        occupied_cells=int((density > 0).sum()),
        total_cells=int(density.size),
    )


def save_density_csv(result: DensityResult, output_path: Path) -> None:
    """Save density grid as flattened CSV."""
    rows = []
    for i in range(result.grid.shape[0]):
        for j in range(result.grid.shape[1]):
            rows.append(
                {
                    "cell_x": i,
                    "cell_y": j,
                    "x_min": float(result.x_edges[i]),
                    "x_max": float(result.x_edges[i + 1]),
                    "y_min": float(result.y_edges[j]),
                    "y_max": float(result.y_edges[j + 1]),
                    "density": float(result.grid[i, j]),
                }
            )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(output_path, index=False)


def plot_density_heatmap(result: DensityResult, output_path: Path, dpi: int = 150) -> None:
    """Render density heatmap to PNG."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 6))
    im = ax.imshow(result.grid.T, origin="lower", cmap="viridis", aspect="auto")
    ax.set_title("Point Density Heatmap")
    ax.set_xlabel("Grid X")
    ax.set_ylabel("Grid Y")
    fig.colorbar(im, ax=ax, label="Density")
    fig.tight_layout()
    fig.savefig(output_path, dpi=dpi)
    plt.close(fig)


def density_histogram(points: np.ndarray, resolution: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Backward-compatible helper returning 2D histogram and edges."""
    res = compute_density_grid(points, DensityConfig(grid_resolution=resolution, density_normalization=False))
    return res.grid, res.x_edges, res.y_edges
