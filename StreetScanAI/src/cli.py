"""Unified command-line interface for StreetScanAI subsystems.

This CLI is a thin orchestration layer over existing modules. It provides:
- argparse subcommands
- optional YAML config defaults
- CLI-over-config override behavior
- direct-import execution with subprocess fallback
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml


def load_yaml_config(config_path: Path | None) -> dict[str, Any]:
    """Load YAML config file safely.

    Returns empty dict when config_path is None or missing (with warning on missing file).
    Raises ValueError for invalid YAML.
    """
    if config_path is None:
        return {}
    if not config_path.exists():
        print(f"[WARN] Config file not found: {config_path}. Using CLI/default values.")
        return {}
    try:
        data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML in config '{config_path}': {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"Config root must be a mapping: {config_path}")
    return data


def get_section_config(config: dict[str, Any], section: str) -> dict[str, Any]:
    """Get command section config or empty dict."""
    sec = config.get(section, {})
    return sec if isinstance(sec, dict) else {}


def merge_args_with_config(args: argparse.Namespace, section_config: dict[str, Any]) -> dict[str, Any]:
    """Merge section config with explicit CLI arguments.

    CLI values override config only when they are not None.
    """
    merged: dict[str, Any] = dict(section_config)
    for key, value in vars(args).items():
        if key in {"command", "config"}:
            continue
        if value is not None:
            merged[key] = value
    return merged


def run_python_module(module_path: Path, arguments: dict[str, Any]) -> int:
    """Run module script via subprocess fallback."""
    cmd = [sys.executable, str(module_path)]
    for key, value in arguments.items():
        if value is None:
            continue
        flag = f"--{key.replace('_', '-')}"
        if isinstance(value, bool):
            if value:
                cmd.append(flag)
            continue
        if isinstance(value, list):
            cmd.append(flag)
            cmd.extend(str(v) for v in value)
            continue
        cmd.extend([flag, str(value)])

    print("[INFO] Fallback subprocess:", " ".join(cmd))
    proc = subprocess.run(cmd, check=False)
    return int(proc.returncode)


def ensure_path_exists(path: Path, kind: str) -> None:
    """Validate required input path exists."""
    if not path.exists():
        raise FileNotFoundError(f"{kind} path does not exist: {path}")


def create_parser() -> argparse.ArgumentParser:
    """Build unified argparse parser."""
    p = argparse.ArgumentParser(description="StreetScanAI unified CLI")
    p.add_argument("--config", default="configs/config.yaml", help="Optional YAML config file path")
    sub = p.add_subparsers(dest="command", required=True)

    pre = sub.add_parser("preprocess", help="Run point cloud preprocessing")
    pre.add_argument("--input", default=None, help="Input point cloud path")
    pre.add_argument("--output-dir", default=None, help="Output directory")
    pre.add_argument("--voxel-size", type=float, default=None, help="Voxel size")
    pre.add_argument("--ground-filter", action="store_true", default=None, help="Enable ground filtering")
    pre.add_argument("--no-ground-filter", action="store_true", default=None, help="Disable ground filtering")
    pre.add_argument("--estimate-density", action="store_true", default=None, help="Enable density estimation")

    clu = sub.add_parser("cluster", help="Run object clustering")
    clu.add_argument("--input", default=None)
    clu.add_argument("--output-dir", default=None)
    clu.add_argument("--method", choices=["dbscan", "euclidean"], default=None)
    clu.add_argument("--eps", type=float, default=None)
    clu.add_argument("--min-points", type=int, default=None)
    clu.add_argument("--min-cluster-size", type=int, default=None)
    clu.add_argument("--save-screenshot", action="store_true", default=None)

    seg = sub.add_parser("segment", help="Run semantic segmentation")
    seg.add_argument("--input", default=None)
    seg.add_argument("--output-dir", default=None)
    seg.add_argument("--method", choices=["baseline", "pointnet"], default=None)
    seg.add_argument("--weights", default=None)
    seg.add_argument("--device", choices=["cpu", "cuda"], default=None)
    seg.add_argument("--cluster-labels", default=None)
    seg.add_argument("--cluster-stats", default=None)

    ana = sub.add_parser("analyze", help="Run urban analytics")
    ana.add_argument("--input", default=None)
    ana.add_argument("--output-dir", default=None)
    ana.add_argument("--semantic-labels", default=None)
    ana.add_argument("--cluster-stats", default=None)
    ana.add_argument("--trajectories", default=None)
    ana.add_argument("--grid-resolution", type=float, default=None)
    ana.add_argument("--save-plots", action="store_true", default=None)

    trk = sub.add_parser("track", help="Run trajectory tracking")
    trk.add_argument("--input", default=None)
    trk.add_argument("--output-dir", default=None)
    trk.add_argument("--fps", type=float, default=None)
    trk.add_argument("--association-distance", type=float, default=None)
    trk.add_argument("--max-missed-frames", type=int, default=None)
    trk.add_argument("--no-kalman", action="store_true", default=None)
    trk.add_argument("--no-smoothing", action="store_true", default=None)
    trk.add_argument("--save-overlay-cloud", action="store_true", default=None)

    vis = sub.add_parser("visualize", help="Generate visualization outputs")
    vis.add_argument("--input", default=None)
    vis.add_argument("--output-dir", default=None)
    vis.add_argument("--semantic-labels", default=None)
    vis.add_argument("--cluster-labels", default=None)
    vis.add_argument("--density-grid", default=None)
    vis.add_argument("--occupancy-grid", default=None)
    vis.add_argument("--trajectories", default=None)
    vis.add_argument("--backend", choices=["open3d", "pyvista"], default=None)
    vis.add_argument("--camera-view", choices=["isometric", "top", "front", "side"], default=None)
    vis.add_argument("--save-animation", action="store_true", default=None)
    vis.add_argument("--interactive", action="store_true", default=None)

    bch = sub.add_parser("benchmark", help="Run benchmark comparison")
    bch.add_argument("--input", default=None)
    bch.add_argument("--output-dir", default=None)
    bch.add_argument("--modes", nargs="+", choices=["preprocessing", "clustering", "segmentation"], default=None)
    bch.add_argument("--ground-truth-labels", default=None)
    bch.add_argument("--repetitions", type=int, default=None)
    bch.add_argument("--warmup-runs", type=int, default=None)

    return p


def _require_input(merged: dict[str, Any], kind: str) -> Path:
    path_str = merged.get("input")
    if not path_str:
        raise ValueError(f"Missing required input for {kind}. Provide --input or set it in config.")
    p = Path(path_str)
    ensure_path_exists(p, "Input")
    return p


def handle_preprocess(merged: dict[str, Any]) -> int:
    _require_input(merged, "preprocess")
    try:
        from src.preprocessing.preprocess_pointcloud import PreprocessingConfig, PointCloudPreprocessor

        cfg = PreprocessingConfig()
        if merged.get("voxel_size") is not None:
            cfg.voxel_size = float(merged["voxel_size"])
        if merged.get("ground_filter"):
            cfg.enable_ground_filtering = True
        if merged.get("no_ground_filter"):
            cfg.enable_ground_filtering = False
        if merged.get("estimate_density"):
            cfg.estimate_density = True

        out_dir = Path(merged.get("output_dir") or "outputs/pointclouds/preprocessed")
        res = PointCloudPreprocessor(cfg).preprocess(Path(merged["input"]), out_dir)
        print(f"[OK] Preprocess done: {res.stats.output_path}")
        return 0
    except Exception as exc:
        print(f"[WARN] Direct preprocess call failed, trying fallback: {exc}")
        return run_python_module(Path("src/preprocessing/preprocess_pointcloud.py"), merged)


def handle_cluster(merged: dict[str, Any]) -> int:
    _require_input(merged, "cluster")
    try:
        from src.clustering.dbscan_clustering import ClusteringConfig, PointCloudClusterer

        cfg = ClusteringConfig()
        for key in ["method", "eps", "min_points", "min_cluster_size", "save_screenshot"]:
            if key in merged and merged[key] is not None and hasattr(cfg, key):
                setattr(cfg, key, merged[key])
        out_dir = Path(merged.get("output_dir") or "outputs/clusters")
        PointCloudClusterer(cfg).cluster_file(Path(merged["input"]), out_dir)
        print(f"[OK] Cluster done: {out_dir}")
        return 0
    except Exception as exc:
        print(f"[WARN] Direct cluster call failed, trying fallback: {exc}")
        return run_python_module(Path("src/clustering/dbscan_clustering.py"), merged)


def handle_segment(merged: dict[str, Any]) -> int:
    _require_input(merged, "segment")
    try:
        from src.segmentation.semantic_segmentation import SegmentationConfig, SemanticSegmenter

        cfg = SegmentationConfig()
        mapping = {
            "method": "method",
            "weights": "weights_path",
            "device": "device",
            "cluster_labels": "cluster_labels_path",
            "cluster_stats": "cluster_stats_path",
        }
        for k, attr in mapping.items():
            if merged.get(k) is not None:
                setattr(cfg, attr, merged[k])
        if merged.get("cluster_labels") or merged.get("cluster_stats"):
            cfg.use_cluster_features = True
        out_dir = Path(merged.get("output_dir") or "outputs/semantic")
        SemanticSegmenter(cfg).segment_file(Path(merged["input"]), out_dir)
        print(f"[OK] Segment done: {out_dir}")
        return 0
    except Exception as exc:
        print(f"[WARN] Direct segment call failed, trying fallback: {exc}")
        return run_python_module(Path("src/segmentation/semantic_segmentation.py"), merged)


def handle_analyze(merged: dict[str, Any]) -> int:
    _require_input(merged, "analyze")
    for key in ["semantic_labels", "cluster_stats", "trajectories"]:
        if merged.get(key) and not Path(str(merged[key])).exists():
            print(f"[WARN] Optional file missing: {merged[key]}")
    try:
        from src.analytics.analytics_pipeline import AnalyticsConfig, UrbanAnalyticsPipeline

        cfg = AnalyticsConfig()
        mapping = {
            "semantic_labels": "semantic_labels_path",
            "cluster_stats": "cluster_stats_path",
            "trajectories": "trajectory_path",
            "grid_resolution": "grid_resolution",
            "save_plots": "save_plots",
        }
        for k, attr in mapping.items():
            if merged.get(k) is not None:
                setattr(cfg, attr, merged[k])
        out_dir = Path(merged.get("output_dir") or "outputs/analytics")
        UrbanAnalyticsPipeline(cfg).run(Path(merged["input"]), out_dir)
        print(f"[OK] Analyze done: {out_dir}")
        return 0
    except Exception as exc:
        print(f"[WARN] Direct analyze call failed, trying fallback: {exc}")
        return run_python_module(Path("src/analytics/analytics_pipeline.py"), merged)


def handle_track(merged: dict[str, Any]) -> int:
    _require_input(merged, "track")
    try:
        from src.tracking.tracking_pipeline import TrackingPipelineConfig, TrackingPipeline

        cfg = TrackingPipelineConfig()
        mapping = {
            "fps": "fps",
            "association_distance": "association_distance_threshold",
            "max_missed_frames": "max_missed_frames",
            "save_overlay_cloud": "save_overlay_cloud",
        }
        for k, attr in mapping.items():
            if merged.get(k) is not None:
                setattr(cfg, attr, merged[k])
        if merged.get("no_kalman"):
            cfg.enable_kalman_filter = False
        if merged.get("no_smoothing"):
            cfg.enable_smoothing = False
        out_dir = Path(merged.get("output_dir") or "outputs/trajectories")
        TrackingPipeline(cfg).run(Path(merged["input"]), out_dir)
        print(f"[OK] Track done: {out_dir}")
        return 0
    except Exception as exc:
        print(f"[WARN] Direct track call failed, trying fallback: {exc}")
        return run_python_module(Path("src/tracking/tracking_pipeline.py"), merged)


def handle_visualize(merged: dict[str, Any]) -> int:
    _require_input(merged, "visualize")
    try:
        from src.visualization.visualization_pipeline import VisualizationConfig, VisualizationPipeline

        cfg = VisualizationConfig()
        mapping = {
            "semantic_labels": "semantic_labels_path",
            "cluster_labels": "cluster_labels_path",
            "density_grid": "density_grid_path",
            "occupancy_grid": "occupancy_grid_path",
            "trajectories": "trajectories_path",
            "backend": "backend",
            "camera_view": "camera_view",
            "save_animation": "save_animation",
            "interactive": "interactive",
        }
        for k, attr in mapping.items():
            if merged.get(k) is not None:
                setattr(cfg, attr, merged[k])
        out_dir = Path(merged.get("output_dir") or "outputs/visualizations")
        VisualizationPipeline(cfg).run(Path(merged["input"]), out_dir)
        print(f"[OK] Visualize done: {out_dir}")
        return 0
    except Exception as exc:
        print(f"[WARN] Direct visualize call failed, trying fallback: {exc}")
        return run_python_module(Path("src/visualization/visualization_pipeline.py"), merged)


def handle_benchmark(merged: dict[str, Any]) -> int:
    _require_input(merged, "benchmark")
    try:
        from src.benchmark.benchmark_runner import BenchmarkConfig, BenchmarkRunner

        cfg = BenchmarkConfig()
        mapping = {
            "input": "input",
            "output_dir": "output_dir",
            "modes": "modes",
            "ground_truth_labels": "ground_truth_labels",
            "repetitions": "repetitions",
            "warmup_runs": "warmup_runs",
        }
        for k, attr in mapping.items():
            if merged.get(k) is not None:
                setattr(cfg, attr, merged[k])
        res = BenchmarkRunner(cfg).run()
        print(f"[OK] Benchmark done: {res.results_csv}")
        return 0
    except Exception as exc:
        print(f"[WARN] Direct benchmark call failed, trying fallback: {exc}")
        return run_python_module(Path("src/benchmark/benchmark_runner.py"), merged)


def main() -> None:
    """CLI entrypoint."""
    parser = create_parser()
    args = parser.parse_args()

    try:
        config = load_yaml_config(Path(args.config) if args.config else None)
    except Exception as exc:
        print(f"[ERROR] {exc}")
        sys.exit(2)

    section_map = {
        "preprocess": "preprocessing",
        "cluster": "clustering",
        "segment": "segmentation",
        "analyze": "analytics",
        "track": "tracking",
        "visualize": "visualization",
        "benchmark": "benchmark",
    }
    section = section_map.get(args.command, "")
    section_cfg = get_section_config(config, section)
    merged = merge_args_with_config(args, section_cfg)

    handlers = {
        "preprocess": handle_preprocess,
        "cluster": handle_cluster,
        "segment": handle_segment,
        "analyze": handle_analyze,
        "track": handle_track,
        "visualize": handle_visualize,
        "benchmark": handle_benchmark,
    }

    try:
        code = handlers[args.command](merged)
    except FileNotFoundError as exc:
        print(f"[ERROR] {exc}")
        sys.exit(2)
    except ValueError as exc:
        print(f"[ERROR] {exc}")
        sys.exit(2)
    except Exception as exc:
        print(f"[ERROR] Command failed: {exc}")
        sys.exit(1)

    sys.exit(code)


if __name__ == "__main__":
    main()
