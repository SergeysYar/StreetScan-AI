"""Approximate radial visibility analysis for LiDAR scenes."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


@dataclass
class VisibilityConfig:
    """Configuration for visibility profile estimation."""

    sensor_origin: list[float]
    max_range: float = 80.0
    angle_step_deg: float = 1.0
    range_bins: int = 80


@dataclass
class VisibilityResult:
    """Per-angle visibility summary."""

    angle_deg: np.ndarray
    min_range: np.ndarray
    max_range_vals: np.ndarray
    point_count: np.ndarray
    visible_range_estimate: np.ndarray
    coverage_ratio: float


def compute_visibility_profile(points: np.ndarray, config: VisibilityConfig) -> VisibilityResult:
    """Compute approximate radial visibility profile in XY plane."""
    if len(config.sensor_origin) != 3:
        raise ValueError("sensor_origin must contain exactly 3 values")
    if config.max_range <= 0:
        raise ValueError("max_range must be > 0")
    if config.angle_step_deg <= 0:
        raise ValueError("visibility_angle_step_deg must be > 0")
    if len(points) == 0:
        raise ValueError("Cannot compute visibility for empty point array")

    origin = np.asarray(config.sensor_origin, dtype=float)
    rel = points[:, :2] - origin[:2]
    ranges = np.linalg.norm(rel, axis=1)
    angles = (np.degrees(np.arctan2(rel[:, 1], rel[:, 0])) + 360.0) % 360.0

    bins = np.arange(0.0, 360.0 + config.angle_step_deg, config.angle_step_deg)
    idx = np.digitize(angles, bins) - 1
    n = len(bins) - 1
    min_r = np.full(n, np.nan)
    max_r = np.full(n, np.nan)
    counts = np.zeros(n, dtype=int)
    vis = np.zeros(n, dtype=float)

    for i in range(n):
        mask = idx == i
        if not np.any(mask):
            continue
        r = ranges[mask]
        counts[i] = int(mask.sum())
        min_r[i] = float(r.min())
        max_r[i] = float(r.max())
        vis[i] = min(float(r.max()), config.max_range)

    coverage = float(np.isfinite(max_r).sum() / n)
    centers = (bins[:-1] + bins[1:]) / 2.0
    return VisibilityResult(centers, min_r, max_r, counts, vis, coverage)


def save_visibility_csv(result: VisibilityResult, output_path: Path) -> None:
    """Save visibility profile CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(
        {
            "angle_deg": result.angle_deg,
            "min_range": result.min_range,
            "max_range": result.max_range_vals,
            "point_count": result.point_count,
            "visible_range_estimate": result.visible_range_estimate,
        }
    )
    df.to_csv(output_path, index=False)


def plot_visibility_profile(result: VisibilityResult, output_path: Path, dpi: int = 150) -> None:
    """Plot radial visibility estimate by angle."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(result.angle_deg, result.visible_range_estimate, color="#0f766e", linewidth=1.5)
    ax.set_title("Approximate Radial Visibility Profile")
    ax.set_xlabel("Angle (deg)")
    ax.set_ylabel("Visible Range Estimate (m)")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(output_path, dpi=dpi)
    plt.close(fig)


def visible_ratio(points: np.ndarray, z_threshold: float) -> float:
    """Backward-compatible visibility proxy."""
    if len(points) == 0:
        return 0.0
    return float((points[:, 2] > z_threshold).sum() / len(points))
