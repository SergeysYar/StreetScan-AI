"""Unified command-line interface for StreetScanAI."""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from src.analytics.analytics_pipeline import (
    AnalyticsConfig,
    UrbanAnalyticsPipeline,
    load_analytics_config,
)
from src.analytics.density_analysis import density_histogram
from src.benchmark.benchmark_runner import BenchmarkConfig, run_benchmark
from src.benchmark.report_generator import generate_markdown_report
from src.clustering.dbscan_clustering import (
    ClusteringConfig,
    PointCloudClusterer,
    load_clustering_config,
)
from src.io.load_pointcloud import load_point_cloud, to_numpy
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
from src.tracking.tracking_pipeline import (
    TrackingPipeline,
    TrackingPipelineConfig,
    load_tracking_config,
)
from src.visualization.visualization_pipeline import (
    VisualizationConfig,
    VisualizationPipeline,
    load_visualization_config,
)
from src.visualization.plot_metrics import plot_runtime
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

    analyze_cmd = sub.add_parser("analyze")
    analyze_cmd.add_argument("--input", required=True)
    analyze_cmd.add_argument("--output-dir", default="outputs/analytics")
    analyze_cmd.add_argument("--semantic-labels", default=None)
    analyze_cmd.add_argument("--cluster-stats", default=None)
    analyze_cmd.add_argument("--trajectories", default=None)
    analyze_cmd.add_argument("--grid-resolution", type=float, default=None)
    analyze_cmd.add_argument("--occupancy-threshold", type=int, default=None)
    analyze_cmd.add_argument("--sensor-origin", nargs=3, type=float, default=None)
    analyze_cmd.add_argument("--save-plots", action="store_true")

    track_cmd = sub.add_parser("track")
    track_cmd.add_argument("--input", required=True)
    track_cmd.add_argument("--output-dir", default="outputs/trajectories")
    track_cmd.add_argument("--fps", type=float, default=None)
    track_cmd.add_argument("--association-distance", type=float, default=None)
    track_cmd.add_argument("--max-missed-frames", type=int, default=None)
    track_cmd.add_argument("--min-track-length", type=int, default=None)
    track_cmd.add_argument("--no-kalman", action="store_true")
    track_cmd.add_argument("--no-smoothing", action="store_true")
    track_cmd.add_argument("--smoothing-window", type=int, default=None)
    track_cmd.add_argument("--save-overlay-cloud", action="store_true")

    visualize_cmd = sub.add_parser("visualize")
    visualize_cmd.add_argument("--input", required=True)
    visualize_cmd.add_argument("--output-dir", default="outputs/visualizations")
    visualize_cmd.add_argument("--semantic-labels", default=None)
    visualize_cmd.add_argument("--cluster-labels", default=None)
    visualize_cmd.add_argument("--density-grid", default=None)
    visualize_cmd.add_argument("--occupancy-grid", default=None)
    visualize_cmd.add_argument("--trajectories", default=None)
    visualize_cmd.add_argument("--backend", choices=["open3d", "pyvista"], default=None)
    visualize_cmd.add_argument("--camera-view", choices=["isometric", "top", "front", "side"], default=None)
    visualize_cmd.add_argument("--save-animation", action="store_true")
    visualize_cmd.add_argument("--interactive", action="store_true")

    for name in ["benchmark", "generate-report"]:
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

    if args.command == "analyze":
        base_cfg = load_analytics_config(Path(args.config) if args.config else None)
        merged = AnalyticsConfig(**base_cfg.__dict__)
        if args.semantic_labels is not None:
            merged.semantic_labels_path = args.semantic_labels
        if args.cluster_stats is not None:
            merged.cluster_stats_path = args.cluster_stats
        if args.trajectories is not None:
            merged.trajectory_path = args.trajectories
        if args.grid_resolution is not None:
            merged.grid_resolution = args.grid_resolution
        if args.occupancy_threshold is not None:
            merged.occupancy_threshold = args.occupancy_threshold
        if args.sensor_origin is not None:
            merged.sensor_origin = [float(v) for v in args.sensor_origin]
        if args.save_plots:
            merged.save_plots = True
        UrbanAnalyticsPipeline(merged).run(Path(args.input), Path(args.output_dir))
        return
    if args.command == "track":
        base_cfg = load_tracking_config(Path(args.config) if args.config else None)
        merged = TrackingPipelineConfig(**base_cfg.__dict__)
        if args.fps is not None:
            merged.fps = args.fps
        if args.association_distance is not None:
            merged.association_distance_threshold = args.association_distance
        if args.max_missed_frames is not None:
            merged.max_missed_frames = args.max_missed_frames
        if args.min_track_length is not None:
            merged.min_track_length = args.min_track_length
        if args.no_kalman:
            merged.enable_kalman_filter = False
        if args.no_smoothing:
            merged.enable_smoothing = False
        if args.smoothing_window is not None:
            merged.smoothing_window = args.smoothing_window
        if args.save_overlay_cloud:
            merged.save_overlay_cloud = True
        TrackingPipeline(merged).run(Path(args.input), Path(args.output_dir))
        return
    if args.command == "visualize":
        base_cfg = load_visualization_config(Path(args.config) if args.config else None)
        merged = VisualizationConfig(**base_cfg.__dict__)
        if args.semantic_labels is not None:
            merged.semantic_labels_path = args.semantic_labels
        if args.cluster_labels is not None:
            merged.cluster_labels_path = args.cluster_labels
        if args.density_grid is not None:
            merged.density_grid_path = args.density_grid
        if args.occupancy_grid is not None:
            merged.occupancy_grid_path = args.occupancy_grid
        if args.trajectories is not None:
            merged.trajectories_path = args.trajectories
        if args.backend is not None:
            merged.backend = args.backend
        if args.camera_view is not None:
            merged.camera_view = args.camera_view
        if args.save_animation:
            merged.save_animation = True
        if args.interactive:
            merged.interactive = True
        VisualizationPipeline(merged).run(Path(args.input), Path(args.output_dir))
        return

    cfg = load_project_config(args.config)
    input_path = Path(args.input)
    cloud = load_point_cloud(input_path)
    if args.command == "benchmark":
        result = run_benchmark(cloud, BenchmarkConfig(**cfg["benchmark"]))
        result.to_csv("outputs/benchmarks/benchmark_results.csv", index=False)
        plot_runtime(result, Path("outputs/benchmarks/runtime_plot.png"))
        generate_markdown_report(result, Path("outputs/benchmarks/benchmark_report.md"))
    elif args.command == "generate-report":
        df = pd.read_csv("outputs/benchmarks/benchmark_results.csv")
        generate_markdown_report(df, Path("outputs/reports/final_benchmark_report.md"))


if __name__ == "__main__":
    main()
