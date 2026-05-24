"""Unified command-line interface for StreetScanAI."""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import open3d as o3d

from src.analytics.density_analysis import density_histogram
from src.analytics.spatial_statistics import spatial_stats
from src.benchmark.benchmark_runner import BenchmarkConfig, run_benchmark
from src.benchmark.report_generator import generate_markdown_report
from src.clustering.cluster_analysis import extract_cluster_stats
from src.clustering.dbscan_clustering import run_dbscan
from src.io.load_pointcloud import load_point_cloud, to_numpy
from src.io.save_pointcloud import save_point_cloud
from src.preprocessing.preprocess_pipeline import PreprocessConfig, run_preprocessing
from src.segmentation.semantic_coloring import labels_to_colors
from src.segmentation.semantic_segmentation import segment_points
from src.tracking.trajectory_builder import build_trajectories
from src.tracking.velocity_estimation import estimate_velocity
from src.visualization.heatmap_visualizer import save_heatmap
from src.visualization.plot_metrics import plot_runtime
from src.visualization.trajectory_visualizer import render_trajectories
from src.utils.cli_utils import load_project_config


def main() -> None:
    parser = argparse.ArgumentParser(description="StreetScanAI unified CLI")
    parser.add_argument("--config", default="configs/config.yaml")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ["preprocess", "cluster", "segment", "analyze", "track", "visualize", "benchmark", "generate-report"]:
        cmd = sub.add_parser(name)
        cmd.add_argument("--input", default="data/raw/sample.ply")
    args = parser.parse_args()

    cfg = load_project_config(args.config)
    input_path = Path(args.input)
    cloud = load_point_cloud(input_path)

    if args.command == "preprocess":
        p = PreprocessConfig(**cfg["preprocessing"])
        out = run_preprocessing(cloud, p)
        save_point_cloud(out, Path("outputs/pointclouds/preprocessed.ply"))
    elif args.command == "cluster":
        labels = run_dbscan(cloud, cfg["clustering"]["dbscan_eps"], cfg["clustering"]["dbscan_min_points"])
        points, _ = to_numpy(cloud)
        extract_cluster_stats(points, labels).to_csv("outputs/clusters/cluster_metrics.csv", index=False)
    elif args.command == "segment":
        points, _ = to_numpy(cloud)
        labels = segment_points(points)
        cloud.colors = o3d.utility.Vector3dVector(labels_to_colors(labels))
        save_point_cloud(cloud, Path("outputs/semantic/semantic_colored.ply"))
    elif args.command == "analyze":
        points, _ = to_numpy(cloud)
        hist, _, _ = density_histogram(points, cfg["analytics"]["grid_resolution"])
        save_heatmap(hist, Path("outputs/plots/density_heatmap.png"))
        pd.DataFrame([spatial_stats(points)]).to_csv("outputs/reports/spatial_stats.csv", index=False)
    elif args.command == "track":
        points, _ = to_numpy(cloud)
        labels = run_dbscan(cloud, 0.8, 12)
        stats = extract_cluster_stats(points, labels)
        stats["frame"] = 0
        tracks = estimate_velocity(build_trajectories(stats))
        tracks.to_csv("outputs/trajectories/tracks.csv", index=False)
        render_trajectories(tracks, Path("outputs/trajectories/trajectories.png"))
    elif args.command == "visualize":
        points, _ = to_numpy(cloud)
        hist, _, _ = density_histogram(points, cfg["analytics"]["grid_resolution"])
        save_heatmap(hist, Path("outputs/plots/scene_heatmap.png"), title="Scene Density")
    elif args.command == "benchmark":
        result = run_benchmark(cloud, BenchmarkConfig(**cfg["benchmark"]))
        result.to_csv("outputs/benchmarks/benchmark_results.csv", index=False)
        plot_runtime(result, Path("outputs/benchmarks/runtime_plot.png"))
        generate_markdown_report(result, Path("outputs/benchmarks/benchmark_report.md"))
    elif args.command == "generate-report":
        df = pd.read_csv("outputs/benchmarks/benchmark_results.csv")
        generate_markdown_report(df, Path("outputs/reports/final_benchmark_report.md"))


if __name__ == "__main__":
    main()
