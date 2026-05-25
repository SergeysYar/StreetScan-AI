"""Heatmap visualization."""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


def save_heatmap(hist: np.ndarray, out_path: Path, title: str = "Spatial Density") -> None:
    """Save density heatmap image."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(7, 6))
    im = ax.imshow(hist.T, origin="lower", cmap="magma")
    ax.set_title(title)
    fig.colorbar(im, ax=ax, label="density")
    fig.savefig(out_path, dpi=220, bbox_inches="tight")
    plt.close(fig)
