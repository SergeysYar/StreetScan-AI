"""Benchmark comparison helpers and recommendations."""
from __future__ import annotations

import numpy as np
import pandas as pd


def select_best_by_metric(df: pd.DataFrame, metric: str, higher_is_better: bool) -> dict:
    """Select best experiment row by metric."""
    if metric not in df.columns:
        return {}
    work = df.dropna(subset=[metric])
    if work.empty:
        return {}
    idx = work[metric].idxmax() if higher_is_better else work[metric].idxmin()
    row = work.loc[idx]
    return {
        "experiment_name": row.get("experiment_name"),
        "mode": row.get("mode"),
        "metric": metric,
        "value": row.get(metric),
    }


def rank_experiments(df: pd.DataFrame, metric: str, higher_is_better: bool) -> pd.DataFrame:
    """Rank experiments by selected metric."""
    if metric not in df.columns:
        return pd.DataFrame()
    work = df[["mode", "experiment_name", metric]].dropna().copy()
    if work.empty:
        return work
    work["rank"] = work[metric].rank(ascending=not higher_is_better, method="dense")
    return work.sort_values(["rank", "mode", "experiment_name"]).reset_index(drop=True)


def create_comparison_table(df: pd.DataFrame) -> pd.DataFrame:
    """Create aggregated comparison table by mode and experiment."""
    agg_cols = [c for c in [
        "runtime_mean_sec",
        "points_per_second",
        "point_reduction_ratio",
        "number_of_clusters",
        "mean_cluster_size",
        "segmentation_accuracy",
        "mean_class_accuracy",
    ] if c in df.columns]
    if not agg_cols:
        return pd.DataFrame()
    return df.groupby(["mode", "experiment_name"], as_index=False)[agg_cols].mean(numeric_only=True)


def generate_recommendations(df: pd.DataFrame) -> list[str]:
    """Generate simple data-driven benchmark recommendations."""
    recs: list[str] = []
    if df.empty:
        return ["No benchmark data available for recommendations."]

    if "runtime_mean_sec" in df.columns:
        best_fast = select_best_by_metric(df, "runtime_mean_sec", higher_is_better=False)
        if best_fast:
            recs.append(
                f"Fastest configuration: {best_fast.get('experiment_name')} ({best_fast.get('mode')}) with runtime {best_fast.get('value'):.4f}s."
            )

    if "points_per_second" in df.columns:
        best_pps = select_best_by_metric(df, "points_per_second", higher_is_better=True)
        if best_pps:
            recs.append(
                f"Highest throughput: {best_pps.get('experiment_name')} ({best_pps.get('mode')}) at {best_pps.get('value'):.2f} pts/s."
            )

    if "number_of_clusters" in df.columns and "mean_cluster_size" in df.columns:
        cl = df.dropna(subset=["number_of_clusters", "mean_cluster_size"])
        if not cl.empty:
            cl = cl.assign(cluster_balance=(cl["number_of_clusters"] * np.log1p(cl["mean_cluster_size"])))
            idx = cl["cluster_balance"].idxmax()
            row = cl.loc[idx]
            recs.append(
                f"Best clustering balance proxy: {row['experiment_name']} with {row['number_of_clusters']:.1f} clusters and mean size {row['mean_cluster_size']:.1f}."
            )

    if "segmentation_accuracy" in df.columns:
        seg = df.dropna(subset=["segmentation_accuracy"])
        if not seg.empty:
            idx = seg["segmentation_accuracy"].idxmax()
            row = seg.loc[idx]
            recs.append(
                f"Best segmentation accuracy: {row['experiment_name']} at {row['segmentation_accuracy']:.4f}."
            )
        else:
            recs.append("Segmentation accuracy unavailable: no valid ground-truth comparison provided.")

    if not recs:
        recs.append("Insufficient metrics to derive robust recommendations.")
    return recs


def compare(df: pd.DataFrame) -> pd.DataFrame:
    """Backward-compatible comparison helper."""
    return create_comparison_table(df)
