"""Semantic segmentation pipeline for StreetScanAI."""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, field
from pathlib import Path
from time import perf_counter
from typing import Any

import numpy as np
import open3d as o3d
import pandas as pd
import yaml

from src.segmentation.labels import get_label_name, list_classes
from src.segmentation.pointnet_placeholder import PointNetSegmenter
from src.segmentation.semantic_coloring import colorize_by_labels
from src.segmentation.segmentation_io import (
    load_point_cloud,
    save_labels_csv,
    save_point_cloud,
    save_report_markdown,
    save_stats_csv,
)


@dataclass
class SegmentationConfig:
    """Configuration for semantic segmentation."""

    method: str = "baseline"
    weights_path: str | None = None
    device: str = "cpu"
    use_cluster_features: bool = False
    cluster_labels_path: str | None = None
    cluster_stats_path: str | None = None
    z_ground_threshold: float = 0.25
    z_vehicle_min: float = 0.3
    z_vehicle_max: float = 2.2
    z_pedestrian_min: float = 0.5
    z_pedestrian_max: float = 2.5
    pole_radius_threshold: float = 0.25
    min_points_per_object: int = 20
    save_screenshot: bool = False
    output_format: str = "ply"


@dataclass
class SemanticPrediction:
    """Prediction container."""

    labels: np.ndarray
    label_names: list[str]
    confidence: np.ndarray | None
    method: str


@dataclass
class SegmentationResult:
    """Output summary of segmentation run."""

    input_path: str
    output_cloud_path: str
    labels_path: str
    stats_path: str
    report_path: str
    screenshot_path: str | None
    total_points: int
    class_counts: dict[str, int]
    processing_time_sec: float
    method: str
    warnings: list[str] = field(default_factory=list)


class SemanticSegmenter:
    """Reusable semantic segmentation pipeline."""

    def __init__(self, config: SegmentationConfig) -> None:
        self.config = config
        self.warnings: list[str] = []
        self._validate_config()

    def _validate_config(self) -> None:
        if self.config.method not in {"baseline", "pointnet"}:
            raise ValueError("Unsupported segmentation method. Use 'baseline' or 'pointnet'.")
        if self.config.output_format not in {"ply", "pcd"}:
            raise ValueError("output_format must be 'ply' or 'pcd'.")
        if self.config.min_points_per_object <= 0:
            raise ValueError("min_points_per_object must be > 0.")

    def load_optional_cluster_features(self) -> dict[str, Any]:
        """Load optional cluster labels/statistics if configured."""
        features: dict[str, Any] = {}
        if not self.config.use_cluster_features:
            return features

        if self.config.cluster_labels_path:
            p = Path(self.config.cluster_labels_path)
            if p.exists():
                features["cluster_labels_df"] = pd.read_csv(p)
            else:
                self.warnings.append(f"Cluster labels path not found: {p}")

        if self.config.cluster_stats_path:
            p = Path(self.config.cluster_stats_path)
            if p.exists():
                features["cluster_stats_df"] = pd.read_csv(p)
            else:
                self.warnings.append(f"Cluster stats path not found: {p}")
        return features

    def run_baseline_segmentation(self, points: np.ndarray) -> np.ndarray:
        """Deterministic rule-based baseline semantic segmentation."""
        n = len(points)
        labels = np.zeros(n, dtype=int)
        if n == 0:
            return labels

        z = points[:, 2]
        z_rel = z - float(z.min())

        road_mask = z_rel <= self.config.z_ground_threshold
        labels[road_mask] = 1

        not_road = ~road_mask
        veh_mask = not_road & (z_rel >= self.config.z_vehicle_min) & (z_rel <= self.config.z_vehicle_max)
        labels[veh_mask] = 3

        ped_mask = not_road & (z_rel >= self.config.z_pedestrian_min) & (z_rel <= self.config.z_pedestrian_max)
        labels[ped_mask] = np.where(labels[ped_mask] == 0, 4, labels[ped_mask])

        high_mask = z_rel > self.config.z_vehicle_max
        labels[high_mask] = 2

        # Local density heuristic for vegetation vs building among high points.
        if high_mask.any():
            high_idx = np.where(high_mask)[0]
            subset = points[high_idx]
            radius = 1.0
            # Count neighbors in a simple deterministic manner.
            diffs = subset[:, None, :] - subset[None, :, :]
            d2 = np.sum(diffs * diffs, axis=2)
            neighbor_counts = (d2 <= radius * radius).sum(axis=1)
            sparse = neighbor_counts < np.median(neighbor_counts)
            labels[high_idx[sparse]] = 5
            labels[high_idx[~sparse]] = 2

        # Pole and traffic sign heuristics based on XY compactness at elevated heights.
        elevated_idx = np.where((z_rel > self.config.z_ground_threshold) & (z_rel < self.config.z_pedestrian_max + 1.0))[0]
        if len(elevated_idx) > 0:
            xy = points[elevated_idx, :2]
            center = xy.mean(axis=0)
            radial = np.linalg.norm(xy - center, axis=1)
            thin_mask = radial < self.config.pole_radius_threshold
            pole_candidates = elevated_idx[thin_mask & (z_rel[elevated_idx] > self.config.z_vehicle_min)]
            labels[pole_candidates] = 6
            sign_candidates = elevated_idx[thin_mask & (z_rel[elevated_idx] > self.config.z_pedestrian_max)]
            labels[sign_candidates] = 7

        # Keep unlabeled where rules are uncertain.
        uncertain = (z_rel > self.config.z_ground_threshold) & (labels == 0)
        labels[uncertain] = 0
        return labels

    def run_pointnet_segmentation(self, points: np.ndarray) -> np.ndarray:
        """Invoke PointNet++ placeholder contract."""
        segmenter = PointNetSegmenter(Path(self.config.weights_path) if self.config.weights_path else None, self.config.device)
        return segmenter.predict(points)

    def segment_cloud(self, cloud: o3d.geometry.PointCloud) -> SemanticPrediction:
        """Run segmentation on in-memory point cloud."""
        points = np.asarray(cloud.points)
        if len(points) == 0:
            raise ValueError("Input cloud is empty.")

        if self.config.method == "baseline":
            labels = self.run_baseline_segmentation(points)
            confidence = None
        elif self.config.method == "pointnet":
            labels = self.run_pointnet_segmentation(points)
            confidence = None
        else:
            raise ValueError(f"Unsupported method: {self.config.method}")

        label_names = [get_label_name(int(v)) for v in labels]
        return SemanticPrediction(labels=labels, label_names=label_names, confidence=confidence, method=self.config.method)

    def compute_semantic_statistics(self, labels: np.ndarray) -> dict[str, int]:
        """Compute per-class point counts."""
        stats = {c.name: 0 for c in list_classes()}
        unique, counts = np.unique(labels, return_counts=True)
        for label_id, count in zip(unique.tolist(), counts.tolist()):
            stats[get_label_name(int(label_id))] = int(count)
        return stats

    def _save_screenshot(self, cloud: o3d.geometry.PointCloud, path: Path) -> None:
        """Save Open3D screenshot, if possible."""
        path.parent.mkdir(parents=True, exist_ok=True)
        vis = o3d.visualization.Visualizer()
        vis.create_window(visible=False)
        vis.add_geometry(cloud)
        vis.poll_events()
        vis.update_renderer()
        vis.capture_screen_image(str(path), do_render=True)
        vis.destroy_window()

    def save_outputs(
        self,
        *,
        input_path: Path,
        cloud: o3d.geometry.PointCloud,
        prediction: SemanticPrediction,
        output_dir: Path,
    ) -> tuple[str, str, str, str, str | None, dict[str, int]]:
        """Persist semantic cloud, labels, stats and report assets."""
        output_dir.mkdir(parents=True, exist_ok=True)
        report_dir = Path("outputs/reports/segmentation")
        report_dir.mkdir(parents=True, exist_ok=True)

        base = input_path.stem
        ext = ".ply" if self.config.output_format == "ply" else ".pcd"
        semantic_cloud_path = output_dir / f"{base}_semantic{ext}"
        labels_path = output_dir / f"{base}_semantic_labels.csv"
        stats_path = output_dir / f"{base}_semantic_stats.csv"
        report_path = report_dir / f"{base}_segmentation_report.md"
        screenshot_path = output_dir / f"{base}_semantic.png"

        colored_cloud = colorize_by_labels(cloud, prediction.labels)
        save_point_cloud(colored_cloud, semantic_cloud_path)

        points = np.asarray(cloud.points)
        save_labels_csv(points, prediction.labels, labels_path, prediction.confidence)

        stats = self.compute_semantic_statistics(prediction.labels)
        save_stats_csv(stats, stats_path)

        screenshot_saved: str | None = None
        if self.config.save_screenshot:
            try:
                self._save_screenshot(colored_cloud, screenshot_path)
                screenshot_saved = str(screenshot_path)
            except Exception as exc:
                self.warnings.append(f"Semantic screenshot export failed: {exc}")

        return (
            str(semantic_cloud_path),
            str(labels_path),
            str(stats_path),
            str(report_path),
            screenshot_saved,
            stats,
        )

    def generate_report(self, result: SegmentationResult, stats: dict[str, int], output_path: Path) -> None:
        """Generate Markdown report for segmentation run."""
        save_report_markdown(result, stats, output_path)

    def segment_file(self, input_path: Path, output_dir: Path) -> SegmentationResult:
        """Full segmentation pipeline from file to outputs."""
        t0 = perf_counter()
        self.warnings = []
        cloud = load_point_cloud(input_path)

        if self.config.use_cluster_features:
            _ = self.load_optional_cluster_features()

        prediction = self.segment_cloud(cloud)
        out_cloud, labels_csv, stats_csv, report_md, screenshot, stats = self.save_outputs(
            input_path=input_path,
            cloud=cloud,
            prediction=prediction,
            output_dir=output_dir,
        )

        result = SegmentationResult(
            input_path=str(input_path),
            output_cloud_path=out_cloud,
            labels_path=labels_csv,
            stats_path=stats_csv,
            report_path=report_md,
            screenshot_path=screenshot,
            total_points=len(prediction.labels),
            class_counts=stats,
            processing_time_sec=perf_counter() - t0,
            method=self.config.method,
            warnings=list(self.warnings),
        )
        self.generate_report(result, stats, Path(report_md))
        return result


def load_segmentation_config(config_path: Path | None) -> SegmentationConfig:
    """Load segmentation config from YAML file."""
    if config_path is None:
        return SegmentationConfig()
    if not config_path.exists():
        raise FileNotFoundError(f"Config file does not exist: {config_path}")
    try:
        raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML config '{config_path}': {exc}") from exc
    section = raw.get("segmentation", raw)
    if not isinstance(section, dict):
        raise ValueError(f"Invalid segmentation config format in '{config_path}'.")
    return SegmentationConfig(**section)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="StreetScanAI semantic segmentation")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-dir", default="outputs/semantic")
    parser.add_argument("--config", default="configs/segmentation.yaml")
    parser.add_argument("--method", choices=["baseline", "pointnet"], default=None)
    parser.add_argument("--weights", default=None)
    parser.add_argument("--device", choices=["cpu", "cuda"], default=None)
    parser.add_argument("--cluster-labels", default=None)
    parser.add_argument("--cluster-stats", default=None)
    parser.add_argument("--save-screenshot", action="store_true")
    return parser


def _apply_overrides(config: SegmentationConfig, args: argparse.Namespace) -> SegmentationConfig:
    updated = SegmentationConfig(**asdict(config))
    if args.method is not None:
        updated.method = args.method
    if args.weights is not None:
        updated.weights_path = args.weights
    if args.device is not None:
        updated.device = args.device
    if args.cluster_labels is not None:
        updated.cluster_labels_path = args.cluster_labels
        updated.use_cluster_features = True
    if args.cluster_stats is not None:
        updated.cluster_stats_path = args.cluster_stats
        updated.use_cluster_features = True
    if args.save_screenshot:
        updated.save_screenshot = True
    return updated


def run_from_args(args: argparse.Namespace) -> SegmentationResult:
    """Execute segmentation with argparse namespace."""
    cfg = load_segmentation_config(Path(args.config) if args.config else None)
    cfg = _apply_overrides(cfg, args)
    return SemanticSegmenter(cfg).segment_file(Path(args.input), Path(args.output_dir))


def main() -> None:
    """Direct script entrypoint."""
    parser = _build_parser()
    args = parser.parse_args()
    try:
        result = run_from_args(args)
    except Exception as exc:
        print(f"[ERROR] Segmentation failed: {exc}")
        raise SystemExit(1) from exc
    print(
        "[OK] Segmentation completed. "
        f"Method: {result.method}. "
        f"Points: {result.total_points}."
    )


if __name__ == "__main__":
    main()
