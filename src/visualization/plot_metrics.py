"""Plot benchmark metrics."""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def plot_runtime(df: pd.DataFrame, out_path: Path) -> None:
    """Create runtime comparison bar chart."""
    fig, ax = plt.subplots(figsize=(8, 5))
    grouped = df.groupby("method", as_index=False)["runtime"].mean()
    ax.bar(grouped["method"], grouped["runtime"], color="#2878B5")
    ax.set_ylabel("Runtime (s)")
    ax.set_title("Method Runtime Comparison")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=220, bbox_inches="tight")
    plt.close(fig)
