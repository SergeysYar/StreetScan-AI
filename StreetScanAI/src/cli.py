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
from src.clustering.dbscan_clustering import (
    ClusteringConfig,
    PointCloudClusterer,
    load_clustering_config,
)
from src.clustering.cluster_analysis import extract_cluster_stats
from src.clustering.dbscan_clustering import run_dbscan
from src.io.load_pointcloud import load_point_cloud, to_numpy
from src.io.save_pointcloud import save_point_cloud
from src.preprocessing.preprocess_pointcloud import (
    PointCloudPreprocessor,
    PreprocessingConfig,
    load_preprocessing_config,
)
from src.segmentation.semantic_segmentation import (
    SegmentationConfig,
    SemanticSegmenter,
    load_segmentation_config,
)
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
    preprocess_cmd = sub.add_parser("preprocess")
    preprocess_cmd.add_argument("--input", required=True)
    preprocess_cmd.add_argument("--output-dir", default="outputs/pointclouds/preprocessed")
    preprocess_cmd.add_argument("--voxel-size", type=float, default=None)
    preprocess_cmd.add_argument("--no-downsampling", action="store_true")
    preprocess_cmd.add_argument("--no-statistical-filter", action="store_true")
    preprocess_cmd.add_argument("--radius-filter", action="store_true")
    preprocess_cmd.add_argument("--ground-filter", action="store_true")
    preprocess_cmd.add_argument("--normalize", action="store_true")
    preprocess_cmd.add_argument("--estimate-density", action="store_true")
    preprocess_cmd.add_argument("--output-format", choices=["ply", "pcd"], default=None)

    cluster_cmd = sub.add_parser("cluster")
    cluster_cmd.add_argument("--input", required=True)
    cluster_cmd.add_argument("--output-dir", default="outputs/clusters")
    cluster_cmd.add_argument("--method", choices=["dbscan", "euclidean"], default=None)
    cluster_cmd.add_argument("--eps", type=float, default=None)
    cluster_cmd.add_argument("--min-points", type=int, default=None)
    cluster_cmd.add_argument("--euclidean-tolerance", type=float, default=None)
    cluster_cmd.add_argument("--min-cluster-size", type=int, default=None)
    cluster_cmd.add_argument("--max-cluster-size", type=int, default=None)
    cluster_cmd.add_argument("--remove-noise", action="store_true")
    cluster_cmd.add_argument("--save-screenshot", action="store_true")

    segment_cmd = sub.add_parser("segment")
    segment_cmd.add_argument("--input", required=True)
    segment_cmd.add_argument("--output-dir", default="outputs/semantic")
    segment_cmd.add_argument("--method", choices=["baseline", "pointnet"], default=None)
    segment_cmd.add_argument("--weights", default=None)
    segment_cmd.add_argument("--device", choices=["cpu", "cuda"], default=None)
    segment_cmd.add_argument("--cluster-labels", default=None)
    segment_cmd.add_argument("--cluster-stats", default=None)
    segment_cmd.add_argument("--save-screenshot", action="store_true")

    for name in ["analyze", "track", "visualize", "benchmark", "generate-report"]:
        cmd = sub.add_parser(name)
        cmd.add_argument("--input", default="data/raw/sample.ply")
    args = parser.parse_args()

    if args.command == "preprocess":
        base_cfg = load_preprocessing_config(Path(args.config) if args.config else None)
        merged = PreprocessingConfig(**base_cfg.__dict__)
        if args.voxel_size is not None:
            merged.voxel_size = args.voxel_size
        if args.no_downsampling:
            merged.enable_voxel_downsampling = False
        if args.no_statistical_filter:
            merged.enable_statistical_outlier_removal = False
        if args.radius_filter:
            merged.enable_radius_outlier_removal = True
        if args.ground_filter:
            merged.enable_ground_filtering = True
        if args.normalize:
            merged.normalize_coordinates = True
        if args.estimate_density:
            merged.estimate_density = True
        if args.output_format is not None:
            merged.output_format = args.output_format
        preprocessor = PointCloudPreprocessor(merged)
        preprocessor.preprocess(Path(args.input), Path(args.output_dir))
        return

    if args.command == "cluster":
        base_cfg = load_clustering_config(Path(args.config) if args.config else None)
        merged = ClusteringConfig(**base_cfg.__dict__)
        if args.method is not None:
            merged.method = args.method
        if args.eps is not None:
            merged.eps = args.eps
        if args.min_points is not None:
            merged.min_points = args.min_points
        if args.euclidean_tolerance is not None:
            merged.euclidean_tolerance = args.euclidean_tolerance
        if args.min_cluster_size is not None:
            merged.min_cluster_size = args.min_cluster_size
        if args.max_cluster_size is not None:
            merged.max_cluster_size = args.max_cluster_size
        if args.remove_noise:
            merged.remove_noise = True
        if args.save_screenshot:
            merged.save_screenshot = True
        PointCloudClusterer(merged).cluster_file(Path(args.input), Path(args.output_dir))
        return

    if args.command == "segment":
        base_cfg = load_segmentation_config(Path(args.config) if args.config else None)
        merged = SegmentationConfig(**base_cfg.__dict__)
        if args.method is not None:
            merged.method = args.method
        if args.weights is not None:
            merged.weights_path = args.weights
        if args.device is not None:
            merged.device = args.device
        if args.cluster_labels is not None:
            merged.cluster_labels_path = args.cluster_labels
            merged.use_cluster_features = True
        if args.cluster_stats is not None:
            merged.cluster_stats_path = args.cluster_stats
            merged.use_cluster_features = True
        if args.save_screenshot:
            merged.save_screenshot = True
        SemanticSegmenter(merged).segment_file(Path(args.input), Path(args.output_dir))
        return

    cfg = load_project_config(args.config)
    input_path = Path(args.input)
    cloud = load_point_cloud(input_path)
    if args.command == "analyze":
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
