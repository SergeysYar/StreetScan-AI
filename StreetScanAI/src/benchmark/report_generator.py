"""Benchmark markdown report generation."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.benchmark.compare_methods import generate_recommendations


def generate_benchmark_report(
    results_df: pd.DataFrame,
    summary: dict,
    plot_paths: list[Path],
    output_path: Path,
) -> None:
    """Generate full benchmark markdown report."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    failed = results_df[results_df["status"] != "success"] if "status" in results_df.columns else pd.DataFrame()
    best_runtime = results_df.sort_values("runtime_mean_sec").head(1) if "runtime_mean_sec" in results_df.columns else pd.DataFrame()
    best_pps = results_df.sort_values("points_per_second", ascending=False).head(1) if "points_per_second" in results_df.columns else pd.DataFrame()

    lines = [
        "# Benchmark Report",
        "",
        "## 1. Benchmark overview",
        f"- total_runs: {summary.get('total_runs')}",
        f"- successful_runs: {summary.get('successful_runs')}",
        f"- failed_runs: {summary.get('failed_runs')}",
        "",
        "## 2. Input data",
        f"- input_files: {summary.get('input_files')}",
        f"- modes: {summary.get('modes')}",
        "",
        "## 3. Compared experiment groups",
        f"- preprocessing: {int((results_df['mode'] == 'preprocessing').sum()) if 'mode' in results_df.columns else 0}",
        f"- clustering: {int((results_df['mode'] == 'clustering').sum()) if 'mode' in results_df.columns else 0}",
        f"- segmentation: {int((results_df['mode'] == 'segmentation').sum()) if 'mode' in results_df.columns else 0}",
        "",
        "## 4. Runtime comparison",
    ]

    if not best_runtime.empty:
        r = best_runtime.iloc[0]
        lines.append(f"Fastest: `{r.get('experiment_name')}` ({r.get('mode')}) = {r.get('runtime_mean_sec'):.6f}s")
    else:
        lines.append("Unavailable")

    lines.extend([
        "",
        "## 5. Preprocessing comparison",
        "| Experiment | Runtime Mean (s) | Reduction |",
        "|---|---:|---:|",
    ])
    pre = results_df[results_df.get("mode") == "preprocessing"] if "mode" in results_df.columns else pd.DataFrame()
    for _, row in pre.iterrows():
        lines.append(f"| {row.get('experiment_name')} | {row.get('runtime_mean_sec', float('nan')):.6f} | {row.get('point_reduction_ratio', float('nan'))} |")
    if pre.empty:
        lines.append("| n/a | n/a | n/a |")

    lines.extend([
        "",
        "## 6. Clustering comparison",
        "| Experiment | Runtime Mean (s) | Cluster Count | Mean Cluster Size |",
        "|---|---:|---:|---:|",
    ])
    cl = results_df[results_df.get("mode") == "clustering"] if "mode" in results_df.columns else pd.DataFrame()
    for _, row in cl.iterrows():
        lines.append(f"| {row.get('experiment_name')} | {row.get('runtime_mean_sec', float('nan')):.6f} | {row.get('number_of_clusters', float('nan'))} | {row.get('mean_cluster_size', float('nan'))} |")
    if cl.empty:
        lines.append("| n/a | n/a | n/a | n/a |")

    lines.extend([
        "",
        "## 7. Segmentation comparison",
        "| Experiment | Runtime Mean (s) | Segmentation Accuracy | Mean Class Accuracy |",
        "|---|---:|---:|---:|",
    ])
    sg = results_df[results_df.get("mode") == "segmentation"] if "mode" in results_df.columns else pd.DataFrame()
    for _, row in sg.iterrows():
        lines.append(f"| {row.get('experiment_name')} | {row.get('runtime_mean_sec', float('nan')):.6f} | {row.get('segmentation_accuracy', '')} | {row.get('mean_class_accuracy', '')} |")
    if sg.empty:
        lines.append("| n/a | n/a | n/a | n/a |")

    lines.extend([
        "",
        "## 8. Best configurations",
    ])
    if not best_runtime.empty:
        lines.append(f"- Best runtime: {best_runtime.iloc[0].get('experiment_name')}")
    if not best_pps.empty:
        lines.append(f"- Best points_per_second: {best_pps.iloc[0].get('experiment_name')}")

    lines.extend([
        "",
        "## 9. Recommendations",
    ])
    for rec in generate_recommendations(results_df):
        lines.append(f"- {rec}")

    lines.extend([
        "",
        "## 10. Failed runs",
        "| run_id | mode | experiment_name | error_message |",
        "|---|---|---|---|",
    ])
    for _, row in failed.iterrows():
        lines.append(f"| {row.get('run_id')} | {row.get('mode')} | {row.get('experiment_name')} | {row.get('error_message')} |")
    if failed.empty:
        lines.append("| n/a | n/a | n/a | n/a |")

    lines.extend([
        "",
        "## 11. Limitations",
        "- Missing optional data (e.g. GT labels) leads to unavailable metrics.",
        "- Segment/clustering quality proxies depend on exported stats availability.",
        "",
        "## 12. Reproducibility command",
        "```bash",
        "python src/benchmark/benchmark_runner.py --input <path> --output-dir outputs/benchmarks --config configs/benchmark.yaml",
        "```",
        "",
        "## Plots",
    ])
    for p in plot_paths:
        lines.append(f"- `{p}`")

    output_path.write_text("\n".join(lines), encoding="utf-8")


def generate_markdown_report(df: pd.DataFrame, out_path: Path) -> None:
    """Backward-compatible short report wrapper."""
    summary = {
        "total_runs": int(df.shape[0]),
        "successful_runs": int((df.get("status", pd.Series(dtype=str)) == "success").sum()) if "status" in df.columns else int(df.shape[0]),
        "failed_runs": int((df.get("status", pd.Series(dtype=str)) != "success").sum()) if "status" in df.columns else 0,
        "input_files": sorted(set(df.get("input_file", pd.Series(dtype=str)).astype(str).tolist())) if "input_file" in df.columns else [],
        "modes": sorted(set(df.get("mode", pd.Series(dtype=str)).astype(str).tolist())) if "mode" in df.columns else [],
    }
    generate_benchmark_report(df, summary, [], out_path)
