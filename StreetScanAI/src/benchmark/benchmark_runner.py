"""Benchmark orchestration for preprocessing, clustering and segmentation modes."""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any, Callable

import numpy as np
import pandas as pd
import yaml

from src.benchmark.benchmark_metrics import (
    compute_cluster_quality,
    compute_point_reduction_ratio,
    compute_points_per_second,
    compute_runtime_stats,
    compute_segmentation_accuracy,
    summarize_benchmark_rows,
)
from src.benchmark.compare_methods import create_comparison_table
from src.benchmark.plot_benchmarks import generate_all_plots
from src.benchmark.report_generator import generate_benchmark_report
from src.clustering.dbscan_clustering import ClusteringConfig, PointCloudClusterer
from src.preprocessing.preprocess_pointcloud import PointCloudPreprocessor, PreprocessingConfig
from src.segmentation.semantic_segmentation import SegmentationConfig, SemanticSegmenter


@dataclass
class BenchmarkConfig:
    """Benchmark run configuration."""

    modes: list[str] = field(default_factory=lambda: ["preprocessing", "clustering", "segmentation"])
    input: str = "data/raw"
    output_dir: str = "outputs/benchmarks"
    repetitions: int = 3
    warmup_runs: int = 1
    random_seed: int = 42
    preprocessing_experiments: list[dict] = field(default_factory=list)
    clustering_experiments: list[dict] = field(default_factory=list)
    segmentation_experiments: list[dict] = field(default_factory=list)
    ground_truth_labels: str | None = None
    metrics: dict[str, Any] = field(default_factory=lambda: {"iou_threshold": 0.5, "ignore_unlabeled": True})


@dataclass
class BenchmarkRunResult:
    """One row of benchmark output."""

    run_id: str
    mode: str
    experiment_name: str
    input_file: str
    runtime_sec: float
    points_in: int
    points_out: int | None
    points_per_second: float | None
    metrics: dict
    status: str
    error_message: str | None


@dataclass
class BenchmarkResult:
    """Full benchmark output with paths and warnings."""

    rows: list[BenchmarkRunResult]
    results_csv: str
    summary_json: str
    report_path: str
    plot_paths: list[str]
    warnings: list[str]


class BenchmarkRunner:
    """Executes StreetScanAI benchmark experiments across selected modes."""

    def __init__(self, config: BenchmarkConfig) -> None:
        self.config = config
        self.warnings: list[str] = []
        if self.config.repetitions <= 0:
            raise ValueError("repetitions must be > 0")
        if self.config.warmup_runs < 0:
            raise ValueError("warmup_runs must be >= 0")
        np.random.seed(self.config.random_seed)

    def discover_inputs(self) -> list[Path]:
        """Discover input point cloud files from file or directory."""
        p = Path(self.config.input)
        if not p.exists():
            raise FileNotFoundError(f"Input path does not exist: {p}")
        if p.is_file():
            if p.suffix.lower() not in {".ply", ".pcd", ".xyz"}:
                raise ValueError(f"Unsupported point cloud extension: {p.suffix}")
            return [p]

        files = sorted([x for x in p.iterdir() if x.is_file() and x.suffix.lower() in {".ply", ".pcd", ".xyz"}], key=lambda x: x.name)
        if not files:
            raise ValueError(f"No supported point cloud files found in directory: {p}")
        return files

    def time_function(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> tuple[Any, float]:
        """Time function execution."""
        t0 = perf_counter()
        out = func(*args, **kwargs)
        dt = perf_counter() - t0
        return out, dt

    def run_preprocessing_experiment(self, input_path: Path, experiment: dict) -> BenchmarkRunResult:
        """Run one preprocessing benchmark experiment."""
        run_id = f"pre_{experiment.get('name','exp')}_{input_path.stem}"
        try:
            pre_cfg = PreprocessingConfig(**{k: v for k, v in experiment.items() if k != "name"})
            pre = PointCloudPreprocessor(pre_cfg)
            times: list[float] = []
            points_out: list[int] = []
            for _ in range(self.config.warmup_runs):
                pre.preprocess(input_path, Path(self.config.output_dir) / "tmp_pre")
            for _ in range(self.config.repetitions):
                result, dt = self.time_function(pre.preprocess, input_path, Path(self.config.output_dir) / "tmp_pre")
                times.append(dt)
                points_out.append(int(result.stats.final_points))

            cloud = pre.load_point_cloud(input_path)
            points_in = int(np.asarray(cloud.points).shape[0])
            stats = compute_runtime_stats(times)
            pps = compute_points_per_second(points_in, stats["runtime_mean_sec"])
            pout = int(np.mean(points_out)) if points_out else None
            metrics = {
                **stats,
                "point_reduction_ratio": compute_point_reduction_ratio(points_in, pout if pout is not None else points_in),
            }
            return BenchmarkRunResult(run_id, "preprocessing", str(experiment.get("name", "pre_exp")), str(input_path), stats["runtime_mean_sec"], points_in, pout, pps, metrics, "success", None)
        except Exception as exc:
            return BenchmarkRunResult(run_id, "preprocessing", str(experiment.get("name", "pre_exp")), str(input_path), np.nan, 0, None, None, {}, "failed", str(exc))

    def run_clustering_experiment(self, input_path: Path, experiment: dict) -> BenchmarkRunResult:
        """Run one clustering benchmark experiment."""
        run_id = f"clu_{experiment.get('name','exp')}_{input_path.stem}"
        try:
            cfg = ClusteringConfig(**{k: v for k, v in experiment.items() if k != "name"})
            clu = PointCloudClusterer(cfg)
            cloud = clu.load_point_cloud(input_path)
            points_in = int(np.asarray(cloud.points).shape[0])

            for _ in range(self.config.warmup_runs):
                clu.cluster(cloud)
            times: list[float] = []
            qmetrics: dict[str, Any] = {}
            for _ in range(self.config.repetitions):
                res, dt = self.time_function(clu.cluster, cloud)
                times.append(dt)
                df = pd.DataFrame([
                    {"point_count": c.point_count, "is_noise": int(c.is_noise)} for c in res.cluster_infos
                ])
                qmetrics = compute_cluster_quality(df)

            stats = compute_runtime_stats(times)
            pps = compute_points_per_second(points_in, stats["runtime_mean_sec"])
            metrics = {**stats, **qmetrics}
            return BenchmarkRunResult(run_id, "clustering", str(experiment.get("name", "clu_exp")), str(input_path), stats["runtime_mean_sec"], points_in, points_in, pps, metrics, "success", None)
        except Exception as exc:
            return BenchmarkRunResult(run_id, "clustering", str(experiment.get("name", "clu_exp")), str(input_path), np.nan, 0, None, None, {}, "failed", str(exc))

    def _load_gt_labels(self) -> np.ndarray | None:
        if self.config.ground_truth_labels is None:
            return None
        p = Path(self.config.ground_truth_labels)
        if not p.exists():
            self.warnings.append(f"Ground truth labels not found: {p}")
            return None
        df = pd.read_csv(p)
        if "label_id" not in df.columns:
            self.warnings.append("Ground truth labels CSV missing label_id column")
            return None
        return df["label_id"].to_numpy(dtype=int)

    def run_segmentation_experiment(self, input_path: Path, experiment: dict) -> BenchmarkRunResult:
        """Run one segmentation benchmark experiment."""
        run_id = f"seg_{experiment.get('name','exp')}_{input_path.stem}"
        try:
            cfg = SegmentationConfig(**{k: v for k, v in experiment.items() if k != "name"})
            seg = SemanticSegmenter(cfg)
            cloud = seg.segment_file if False else None
            from src.segmentation.segmentation_io import load_point_cloud
            o3d_cloud = load_point_cloud(input_path)
            points = np.asarray(o3d_cloud.points)
            points_in = int(points.shape[0])

            for _ in range(self.config.warmup_runs):
                seg.segment_cloud(o3d_cloud)

            times: list[float] = []
            pred_labels: np.ndarray | None = None
            for _ in range(self.config.repetitions):
                pred, dt = self.time_function(seg.segment_cloud, o3d_cloud)
                times.append(dt)
                pred_labels = pred.labels

            stats = compute_runtime_stats(times)
            pps = compute_points_per_second(points_in, stats["runtime_mean_sec"])
            gt = self._load_gt_labels()
            if gt is not None and pred_labels is not None and gt.shape[0] == pred_labels.shape[0]:
                acc = compute_segmentation_accuracy(pred_labels, gt, ignore_unlabeled=bool(self.config.metrics.get("ignore_unlabeled", True)))
            else:
                acc = {
                    "overall_accuracy": np.nan,
                    "per_class_accuracy": {},
                    "mean_class_accuracy": np.nan,
                    "labeled_point_count": 0,
                    "ignored_point_count": 0,
                }
                if gt is None:
                    self.warnings.append("Segmentation accuracy unavailable: ground truth labels were not provided.")
                else:
                    self.warnings.append("Segmentation accuracy unavailable: GT label count mismatch.")

            metrics = {**stats, **acc}
            return BenchmarkRunResult(run_id, "segmentation", str(experiment.get("name", "seg_exp")), str(input_path), stats["runtime_mean_sec"], points_in, points_in, pps, metrics, "success", None)
        except Exception as exc:
            return BenchmarkRunResult(run_id, "segmentation", str(experiment.get("name", "seg_exp")), str(input_path), np.nan, 0, None, None, {}, "failed", str(exc))

    def save_run_metadata(self, run_result: BenchmarkRunResult, output_dir: Path) -> None:
        """Save per-run metadata and metrics JSON."""
        run_dir = output_dir / "runs" / run_result.run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        meta = {
            "run_id": run_result.run_id,
            "mode": run_result.mode,
            "experiment_name": run_result.experiment_name,
            "input_file": run_result.input_file,
            "status": run_result.status,
            "error_message": run_result.error_message,
            "runtime_sec": run_result.runtime_sec,
            "points_in": run_result.points_in,
            "points_out": run_result.points_out,
            "points_per_second": run_result.points_per_second,
        }
        (run_dir / "run_metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
        (run_dir / "metrics.json").write_text(json.dumps(run_result.metrics, indent=2, default=str), encoding="utf-8")

    def save_results(self, rows: list[BenchmarkRunResult], output_dir: Path) -> Path:
        """Save results CSV in required schema."""
        output_dir.mkdir(parents=True, exist_ok=True)
        table_rows: list[dict[str, Any]] = []
        for r in rows:
            m = r.metrics or {}
            table_rows.append(
                {
                    "run_id": r.run_id,
                    "mode": r.mode,
                    "experiment_name": r.experiment_name,
                    "input_file": r.input_file,
                    "repetition_count": self.config.repetitions,
                    "runtime_mean_sec": m.get("runtime_mean_sec"),
                    "runtime_std_sec": m.get("runtime_std_sec"),
                    "runtime_min_sec": m.get("runtime_min_sec"),
                    "runtime_max_sec": m.get("runtime_max_sec"),
                    "points_in": r.points_in,
                    "points_out": r.points_out,
                    "point_reduction_ratio": m.get("point_reduction_ratio"),
                    "points_per_second": r.points_per_second,
                    "number_of_clusters": m.get("number_of_clusters"),
                    "noise_ratio": m.get("noise_ratio"),
                    "mean_cluster_size": m.get("mean_cluster_size"),
                    "segmentation_accuracy": m.get("overall_accuracy"),
                    "mean_class_accuracy": m.get("mean_class_accuracy"),
                    "status": r.status,
                    "error_message": r.error_message,
                }
            )
        df = summarize_benchmark_rows(table_rows)
        path = output_dir / "benchmark_results.csv"
        df.to_csv(path, index=False)
        return path

    def run(self) -> BenchmarkResult:
        """Run full benchmark over discovered inputs and configured experiments."""
        inputs = self.discover_inputs()
        out_dir = Path(self.config.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        rows: list[BenchmarkRunResult] = []
        for inp in inputs:
            if "preprocessing" in self.config.modes:
                for exp in self.config.preprocessing_experiments:
                    rr = self.run_preprocessing_experiment(inp, exp)
                    rows.append(rr)
                    self.save_run_metadata(rr, out_dir)
            if "clustering" in self.config.modes:
                for exp in self.config.clustering_experiments:
                    rr = self.run_clustering_experiment(inp, exp)
                    rows.append(rr)
                    self.save_run_metadata(rr, out_dir)
            if "segmentation" in self.config.modes:
                for exp in self.config.segmentation_experiments:
                    rr = self.run_segmentation_experiment(inp, exp)
                    rows.append(rr)
                    self.save_run_metadata(rr, out_dir)

        results_csv = self.save_results(rows, out_dir)
        df = pd.read_csv(results_csv)
        comp = create_comparison_table(df)

        plot_dir = Path("outputs/plots/benchmarks")
        plot_paths = generate_all_plots(comp if not comp.empty else df, plot_dir, dpi=150)

        successful = int((df["status"] == "success").sum()) if "status" in df.columns else int(df.shape[0])
        failed = int((df["status"] != "success").sum()) if "status" in df.columns else 0

        summary = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "input_files": [str(p) for p in inputs],
            "modes": self.config.modes,
            "total_runs": int(df.shape[0]),
            "successful_runs": successful,
            "failed_runs": failed,
            "best_runtime": (df.loc[df["runtime_mean_sec"].idxmin(), ["experiment_name", "runtime_mean_sec"]].to_dict() if "runtime_mean_sec" in df.columns and df["runtime_mean_sec"].notna().any() else None),
            "best_points_per_second": (df.loc[df["points_per_second"].idxmax(), ["experiment_name", "points_per_second"]].to_dict() if "points_per_second" in df.columns and df["points_per_second"].notna().any() else None),
            "best_cluster_quality": (df.loc[df["number_of_clusters"].idxmax(), ["experiment_name", "number_of_clusters"]].to_dict() if "number_of_clusters" in df.columns and df["number_of_clusters"].notna().any() else None),
            "best_segmentation_accuracy": (df.loc[df["segmentation_accuracy"].idxmax(), ["experiment_name", "segmentation_accuracy"]].to_dict() if "segmentation_accuracy" in df.columns and df["segmentation_accuracy"].notna().any() else None),
            "warnings": self.warnings,
        }
        summary_json_path = out_dir / "benchmark_summary.json"
        summary_json_path.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")

        report_path = Path("outputs/reports/benchmark/benchmark_report.md")
        generate_benchmark_report(df, summary, plot_paths, report_path)

        return BenchmarkResult(rows, str(results_csv), str(summary_json_path), str(report_path), [str(p) for p in plot_paths], self.warnings)


def load_benchmark_config(config_path: Path | None) -> BenchmarkConfig:
    """Load benchmark config from YAML file."""
    if config_path is None:
        return BenchmarkConfig()
    if not config_path.exists():
        raise FileNotFoundError(f"Config file does not exist: {config_path}")
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    section = raw.get("benchmark", raw)
    if not isinstance(section, dict):
        raise ValueError(f"Invalid benchmark config format in '{config_path}'.")
    return BenchmarkConfig(**section)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="StreetScanAI benchmark runner")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-dir", default="outputs/benchmarks")
    parser.add_argument("--config", default="configs/benchmark.yaml")
    parser.add_argument("--modes", nargs="+", choices=["preprocessing", "clustering", "segmentation"], default=None)
    parser.add_argument("--ground-truth-labels", default=None)
    parser.add_argument("--repetitions", type=int, default=None)
    parser.add_argument("--warmup-runs", type=int, default=None)
    return parser


def _apply_overrides(cfg: BenchmarkConfig, args: argparse.Namespace) -> BenchmarkConfig:
    merged = BenchmarkConfig(**asdict(cfg))
    merged.input = args.input
    merged.output_dir = args.output_dir
    if args.modes is not None:
        merged.modes = list(args.modes)
    if args.ground_truth_labels is not None:
        merged.ground_truth_labels = args.ground_truth_labels
    if args.repetitions is not None:
        merged.repetitions = args.repetitions
    if args.warmup_runs is not None:
        merged.warmup_runs = args.warmup_runs
    return merged


def run_from_args(args: argparse.Namespace) -> BenchmarkResult:
    """Execute benchmark from parsed CLI args."""
    cfg = load_benchmark_config(Path(args.config) if args.config else None)
    cfg = _apply_overrides(cfg, args)
    return BenchmarkRunner(cfg).run()


def main() -> None:
    """Direct script entrypoint."""
    parser = _build_parser()
    args = parser.parse_args()
    try:
        result = run_from_args(args)
    except Exception as exc:
        print(f"[ERROR] Benchmark runner failed: {exc}")
        raise SystemExit(1) from exc
    print(f"[OK] Benchmark completed. Results: {result.results_csv}")


# Backward-compatible helpers

def run_benchmark(cloud, cfg):
    """Compatibility shim retained for legacy callers."""
    raise RuntimeError("Legacy run_benchmark(cloud, cfg) is deprecated. Use BenchmarkRunner with file input.")


if __name__ == "__main__":
    main()
