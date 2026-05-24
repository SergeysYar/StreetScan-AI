"""Benchmark report generation."""
from __future__ import annotations

from pathlib import Path

import pandas as pd


def generate_markdown_report(df: pd.DataFrame, out_path: Path) -> None:
    """Create markdown report from benchmark dataframe."""
    summary = df.groupby("method", as_index=False).mean(numeric_only=True)
    lines = ["# Benchmark Report", "", "| Method | Runtime (s) | FPS | Cluster Count |", "|---|---:|---:|---:|"]
    for _, row in summary.iterrows():
        lines.append(f"| {row['method']} | {row['runtime']:.4f} | {row['fps']:.2f} | {row['cluster_count']:.1f} |")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
