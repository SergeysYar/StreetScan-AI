"""LiDAR point cloud preprocessing pipeline for StreetScanAI.

This module provides a reusable preprocessing subsystem with:
- robust Open3D-based loading/saving for .ply/.pcd/.xyz
- configurable denoising and downsampling
- optional RANSAC ground estimation and split
- optional centroid-based coordinate normalization
- density estimation and report/statistics generation
"""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from time import perf_counter
from typing import Any

import numpy as np
import open3d as o3d
import yaml


@dataclass
class PreprocessingConfig:
    """Configuration for point cloud preprocessing."""

    voxel_size: float = 0.1
    enable_voxel_downsampling: bool = True
    enable_statistical_outlier_removal: bool = True
    statistical_nb_neighbors: int = 20
    statistical_std_ratio: float = 2.0
    enable_radius_outlier_removal: bool = False
    radius_nb_points: int = 8
    radius: float = 0.5
    enable_ground_filtering: bool = True
    ground_distance_threshold: float = 0.2
    ground_ransac_n: int = 3
    ground_num_iterations: int = 1000
    normalize_coordinates: bool = False
    estimate_density: bool = True
    output_format: str = "ply"


@dataclass
class PointCloudStats:
    """Processing statistics for one input cloud."""

    input_path: str
    output_path: str
    original_points: int
    after_downsampling_points: int
    after_outlier_removal_points: int
    ground_points: int
    nonground_points: int
    final_points: int
    bounding_box_min: list[float]
    bounding_box_max: list[float]
    centroid: list[float]
    average_density: float | None
    processing_time_sec: float
    operations_applied: list[str]
    warnings: list[str] = field(default_factory=list)
    ground_plane_model: list[float] | None = None


@dataclass
class PreprocessingResult:
    """Output of the preprocessing pipeline."""

    processed_cloud: o3d.geometry.PointCloud
    ground_cloud: o3d.geometry.PointCloud | None
    nonground_cloud: o3d.geometry.PointCloud | None
    stats: PointCloudStats


class PointCloudPreprocessor:
    """Reusable preprocessing class for urban LiDAR point clouds."""

    def __init__(self, config: PreprocessingConfig) -> None:
        """Initialize preprocessor with validated configuration."""
        self.config = config
        self._validate_config()

    def _validate_config(self) -> None:
        if self.config.enable_voxel_downsampling and self.config.voxel_size <= 0:
            raise ValueError("Invalid configuration: voxel_size must be > 0.")
        if self.config.statistical_nb_neighbors <= 0:
            raise ValueError("Invalid configuration: statistical_nb_neighbors must be > 0.")
        if self.config.statistical_std_ratio <= 0:
            raise ValueError("Invalid configuration: statistical_std_ratio must be > 0.")
        if self.config.radius_nb_points <= 0:
            raise ValueError("Invalid configuration: radius_nb_points must be > 0.")
        if self.config.radius <= 0:
            raise ValueError("Invalid configuration: radius must be > 0.")
        if self.config.ground_ransac_n < 3:
            raise ValueError("Invalid configuration: ground_ransac_n must be >= 3.")
        if self.config.ground_num_iterations <= 0:
            raise ValueError("Invalid configuration: ground_num_iterations must be > 0.")
        if self.config.ground_distance_threshold <= 0:
            raise ValueError("Invalid configuration: ground_distance_threshold must be > 0.")
        if self.config.output_format not in {"ply", "pcd"}:
            raise ValueError("Invalid configuration: output_format must be 'ply' or 'pcd'.")

    def load_point_cloud(self, input_path: Path) -> o3d.geometry.PointCloud:
        """Load point cloud from supported format."""
        if not input_path.exists():
            raise FileNotFoundError(f"Input file does not exist: {input_path}")
        if input_path.suffix.lower() not in {".ply", ".pcd", ".xyz"}:
            raise ValueError(f"Unsupported point cloud extension: {input_path.suffix}")
        try:
            cloud = o3d.io.read_point_cloud(str(input_path))
        except Exception as exc:
            raise RuntimeError(f"Failed to read point cloud '{input_path}': {exc}") from exc
        if cloud.is_empty() or len(np.asarray(cloud.points)) == 0:
            raise ValueError(f"Input point cloud is empty: {input_path}")
        return cloud

    def save_point_cloud(self, cloud: o3d.geometry.PointCloud, output_path: Path) -> None:
        """Save point cloud to disk with Open3D."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            ok = o3d.io.write_point_cloud(str(output_path), cloud)
        except Exception as exc:
            raise RuntimeError(f"Failed to save point cloud '{output_path}': {exc}") from exc
        if not ok:
            raise RuntimeError(f"Open3D failed to write point cloud: {output_path}")

    def voxel_downsample(self, cloud: o3d.geometry.PointCloud) -> o3d.geometry.PointCloud:
        """Apply voxel downsampling."""
        return cloud.voxel_down_sample(self.config.voxel_size)

    def remove_statistical_outliers(self, cloud: o3d.geometry.PointCloud) -> o3d.geometry.PointCloud:
        """Remove statistical outliers."""
        filtered, _ = cloud.remove_statistical_outlier(
            nb_neighbors=self.config.statistical_nb_neighbors,
            std_ratio=self.config.statistical_std_ratio,
        )
        return filtered

    def remove_radius_outliers(self, cloud: o3d.geometry.PointCloud) -> o3d.geometry.PointCloud:
        """Remove radius outliers."""
        filtered, _ = cloud.remove_radius_outlier(
            nb_points=self.config.radius_nb_points,
            radius=self.config.radius,
        )
        return filtered

    def estimate_ground_plane(self, cloud: o3d.geometry.PointCloud) -> tuple[list[float], list[int]]:
        """Estimate ground plane via RANSAC."""
        model, inliers = cloud.segment_plane(
            distance_threshold=self.config.ground_distance_threshold,
            ransac_n=self.config.ground_ransac_n,
            num_iterations=self.config.ground_num_iterations,
        )
        return [float(v) for v in model], list(map(int, inliers))

    def split_ground_nonground(
        self,
        cloud: o3d.geometry.PointCloud,
        ground_indices: list[int],
    ) -> tuple[o3d.geometry.PointCloud, o3d.geometry.PointCloud]:
        """Split cloud into ground and non-ground subsets."""
        ground_cloud = cloud.select_by_index(ground_indices)
        nonground_cloud = cloud.select_by_index(ground_indices, invert=True)
        return ground_cloud, nonground_cloud

    def normalize_cloud(self, cloud: o3d.geometry.PointCloud) -> o3d.geometry.PointCloud:
        """Center cloud coordinates around centroid while preserving attributes."""
        points = np.asarray(cloud.points)
        if points.size == 0:
            return cloud
        centroid = points.mean(axis=0)
        translated = points - centroid
        cloud.points = o3d.utility.Vector3dVector(translated)
        return cloud

    def estimate_point_density(self, cloud: o3d.geometry.PointCloud) -> float | None:
        """Estimate approximate point density as N / AABB volume."""
        points = np.asarray(cloud.points)
        if len(points) == 0:
            return None
        min_xyz = points.min(axis=0)
        max_xyz = points.max(axis=0)
        extents = max_xyz - min_xyz
        volume = float(extents[0] * extents[1] * extents[2])
        if volume <= 0 or not np.isfinite(volume):
            return None
        return float(len(points) / volume)

    def compute_stats(
        self,
        *,
        input_path: Path,
        output_path: Path,
        original_points: int,
        after_downsampling_points: int,
        after_outlier_removal_points: int,
        ground_points: int,
        nonground_points: int,
        final_points: int,
        cloud_for_stats: o3d.geometry.PointCloud,
        average_density: float | None,
        processing_time_sec: float,
        operations_applied: list[str],
        warnings: list[str],
        ground_plane_model: list[float] | None,
    ) -> PointCloudStats:
        """Compute statistics dataclass from pipeline outputs."""
        points = np.asarray(cloud_for_stats.points)
        if len(points) == 0:
            bbox_min = [0.0, 0.0, 0.0]
            bbox_max = [0.0, 0.0, 0.0]
            centroid = [0.0, 0.0, 0.0]
        else:
            bbox_min = [float(v) for v in points.min(axis=0)]
            bbox_max = [float(v) for v in points.max(axis=0)]
            centroid = [float(v) for v in points.mean(axis=0)]
        return PointCloudStats(
            input_path=str(input_path),
            output_path=str(output_path),
            original_points=original_points,
            after_downsampling_points=after_downsampling_points,
            after_outlier_removal_points=after_outlier_removal_points,
            ground_points=ground_points,
            nonground_points=nonground_points,
            final_points=final_points,
            bounding_box_min=bbox_min,
            bounding_box_max=bbox_max,
            centroid=centroid,
            average_density=average_density,
            processing_time_sec=float(processing_time_sec),
            operations_applied=operations_applied,
            warnings=warnings,
            ground_plane_model=ground_plane_model,
        )

    def preprocess(self, input_path: Path, output_dir: Path) -> PreprocessingResult:
        """Run full preprocessing pipeline and persist artifacts."""
        t0 = perf_counter()
        warnings: list[str] = []
        operations: list[str] = []

        cloud = self.load_point_cloud(input_path)
        original_points = len(np.asarray(cloud.points))
        working = cloud

        if self.config.enable_voxel_downsampling:
            working = self.voxel_downsample(working)
            operations.append("voxel_downsampling")
        after_downsampling_points = len(np.asarray(working.points))

        if self.config.enable_statistical_outlier_removal:
            working = self.remove_statistical_outliers(working)
            operations.append("statistical_outlier_removal")
        if self.config.enable_radius_outlier_removal:
            working = self.remove_radius_outliers(working)
            operations.append("radius_outlier_removal")
        after_outlier_removal_points = len(np.asarray(working.points))

        ground_cloud: o3d.geometry.PointCloud | None = None
        nonground_cloud: o3d.geometry.PointCloud | None = None
        ground_points = 0
        nonground_points = after_outlier_removal_points
        ground_plane_model: list[float] | None = None

        if self.config.enable_ground_filtering:
            try:
                model, indices = self.estimate_ground_plane(working)
                if len(indices) == 0:
                    warnings.append("Ground plane estimated but no inlier ground points were found.")
                else:
                    ground_plane_model = model
                    ground_cloud, nonground_cloud = self.split_ground_nonground(working, indices)
                    ground_points = len(np.asarray(ground_cloud.points))
                    nonground_points = len(np.asarray(nonground_cloud.points))
                    working = nonground_cloud
                    operations.append("ground_filtering")
            except Exception as exc:
                warnings.append(f"Ground plane estimation failed: {exc}")

        if self.config.normalize_coordinates:
            working = self.normalize_cloud(working)
            operations.append("coordinate_normalization")

        density: float | None = None
        if self.config.estimate_density:
            density = self.estimate_point_density(working)
            operations.append("density_estimation")
            if density is None:
                warnings.append("Density estimation unavailable: invalid or zero bounding box volume.")

        ext = ".ply" if self.config.output_format == "ply" else ".pcd"
        base_name = input_path.stem
        output_dir.mkdir(parents=True, exist_ok=True)
        report_dir = Path("outputs/reports/preprocessing")
        report_dir.mkdir(parents=True, exist_ok=True)

        processed_path = output_dir / f"{base_name}_preprocessed{ext}"
        self.save_point_cloud(working, processed_path)

        ground_path = output_dir / f"{base_name}_ground{ext}"
        nonground_path = output_dir / f"{base_name}_nonground{ext}"
        if ground_cloud is not None:
            self.save_point_cloud(ground_cloud, ground_path)
        if nonground_cloud is not None:
            self.save_point_cloud(nonground_cloud, nonground_path)

        final_points = len(np.asarray(working.points))
        elapsed = perf_counter() - t0
        stats = self.compute_stats(
            input_path=input_path,
            output_path=processed_path,
            original_points=original_points,
            after_downsampling_points=after_downsampling_points,
            after_outlier_removal_points=after_outlier_removal_points,
            ground_points=ground_points,
            nonground_points=nonground_points,
            final_points=final_points,
            cloud_for_stats=working,
            average_density=density,
            processing_time_sec=elapsed,
            operations_applied=operations,
            warnings=warnings,
            ground_plane_model=ground_plane_model,
        )

        stats_path = report_dir / f"{base_name}_stats.json"
        report_path = report_dir / f"{base_name}_report.md"
        self._save_stats_json(stats, stats_path)
        self._save_markdown_report(
            stats=stats,
            report_path=report_path,
            config=self.config,
            ground_plane_model=ground_plane_model,
            output_files={
                "processed": processed_path,
                "ground": ground_path if ground_cloud is not None else None,
                "nonground": nonground_path if nonground_cloud is not None else None,
                "stats_json": stats_path,
                "report_md": report_path,
            },
        )

        return PreprocessingResult(
            processed_cloud=working,
            ground_cloud=ground_cloud,
            nonground_cloud=nonground_cloud,
            stats=stats,
        )

    def _save_stats_json(self, stats: PointCloudStats, path: Path) -> None:
        """Save JSON statistics in JSON-compatible format."""
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = asdict(stats)
        with path.open("w", encoding="utf-8") as file:
            json.dump(payload, file, indent=2, ensure_ascii=False)

    def _save_markdown_report(
        self,
        *,
        stats: PointCloudStats,
        report_path: Path,
        config: PreprocessingConfig,
        ground_plane_model: list[float] | None,
        output_files: dict[str, Path | None],
    ) -> None:
        """Save preprocessing report in Markdown format."""
        report_path.parent.mkdir(parents=True, exist_ok=True)
        plane_line = (
            f"{ground_plane_model[0]:.6f}x + {ground_plane_model[1]:.6f}y + "
            f"{ground_plane_model[2]:.6f}z + {ground_plane_model[3]:.6f} = 0"
            if ground_plane_model is not None
            else "Not available"
        )
        warning_lines = "\n".join(f"- {w}" for w in stats.warnings) if stats.warnings else "- None"
        output_lines = "\n".join(
            f"- `{name}`: `{path}`" for name, path in output_files.items() if path is not None
        )
        report = f"""# Preprocessing Report

## 1. Input file
`{stats.input_path}`

## 2. Processing configuration
```yaml
{yaml.safe_dump({'preprocessing': asdict(config)}, sort_keys=False)}
```

## 3. Operations applied
{', '.join(stats.operations_applied) if stats.operations_applied else 'None'}

## 4. Point count reduction
| Stage | Point Count |
|-------|-------------|
| Original | {stats.original_points} |
| After downsampling | {stats.after_downsampling_points} |
| After outlier removal | {stats.after_outlier_removal_points} |
| Ground points | {stats.ground_points} |
| Non-ground points | {stats.nonground_points} |
| Final | {stats.final_points} |

## 5. Bounding box
- Min: {stats.bounding_box_min}
- Max: {stats.bounding_box_max}

## 6. Centroid
{stats.centroid}

## 7. Ground plane model
{plane_line}

## 8. Density estimate
{stats.average_density if stats.average_density is not None else 'Not available'}

## 9. Output files
{output_lines}

## 10. Warnings
{warning_lines}

Normalization note: if `normalize_coordinates=true`, coordinates are translated so centroid becomes origin.
"""
        report_path.write_text(report, encoding="utf-8")


def load_preprocessing_config(config_path: Path | None) -> PreprocessingConfig:
    """Load preprocessing config from YAML file."""
    if config_path is None:
        return PreprocessingConfig()
    if not config_path.exists():
        raise FileNotFoundError(f"Config file does not exist: {config_path}")
    try:
        with config_path.open("r", encoding="utf-8") as file:
            raw = yaml.safe_load(file) or {}
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML config '{config_path}': {exc}") from exc
    except OSError as exc:
        raise RuntimeError(f"Failed to read config '{config_path}': {exc}") from exc

    section: dict[str, Any]
    if "preprocessing" in raw and isinstance(raw["preprocessing"], dict):
        section = raw["preprocessing"]
    elif isinstance(raw, dict):
        section = raw
    else:
        raise ValueError(f"Invalid config format in '{config_path}'.")
    return PreprocessingConfig(**section)


def _build_arg_parser() -> argparse.ArgumentParser:
    """Build argument parser for direct module execution."""
    parser = argparse.ArgumentParser(description="StreetScanAI point cloud preprocessing")
    parser.add_argument("--input", required=True, help="Input point cloud path (.ply/.pcd/.xyz)")
    parser.add_argument("--output-dir", default="outputs/pointclouds/preprocessed", help="Output directory")
    parser.add_argument("--config", default="configs/preprocessing.yaml", help="Preprocessing config YAML path")
    parser.add_argument("--voxel-size", type=float, default=None, help="Override voxel size")
    parser.add_argument("--no-downsampling", action="store_true", help="Disable voxel downsampling")
    parser.add_argument(
        "--no-statistical-filter",
        action="store_true",
        help="Disable statistical outlier removal",
    )
    parser.add_argument("--radius-filter", action="store_true", help="Enable radius outlier removal")
    parser.add_argument("--ground-filter", action="store_true", help="Enable ground filtering")
    parser.add_argument("--normalize", action="store_true", help="Enable coordinate normalization")
    parser.add_argument("--estimate-density", action="store_true", help="Enable density estimation")
    parser.add_argument("--output-format", choices=["ply", "pcd"], default=None, help="Output format")
    return parser


def _apply_cli_overrides(config: PreprocessingConfig, args: argparse.Namespace) -> PreprocessingConfig:
    """Apply CLI overrides on top of config defaults."""
    updated = PreprocessingConfig(**asdict(config))
    if args.voxel_size is not None:
        updated.voxel_size = args.voxel_size
    if args.no_downsampling:
        updated.enable_voxel_downsampling = False
    if args.no_statistical_filter:
        updated.enable_statistical_outlier_removal = False
    if args.radius_filter:
        updated.enable_radius_outlier_removal = True
    if args.ground_filter:
        updated.enable_ground_filtering = True
    if args.normalize:
        updated.normalize_coordinates = True
    if args.estimate_density:
        updated.estimate_density = True
    if args.output_format is not None:
        updated.output_format = args.output_format
    return updated


def run_from_args(args: argparse.Namespace) -> PreprocessingResult:
    """Execute preprocessing from parsed argparse namespace."""
    cfg_path = Path(args.config) if args.config else None
    config = load_preprocessing_config(cfg_path)
    config = _apply_cli_overrides(config, args)
    preprocessor = PointCloudPreprocessor(config)
    return preprocessor.preprocess(Path(args.input), Path(args.output_dir))


def main() -> None:
    """CLI entrypoint for preprocessing-only script."""
    parser = _build_arg_parser()
    args = parser.parse_args()
    try:
        result = run_from_args(args)
    except Exception as exc:
        print(f"[ERROR] Preprocessing failed: {exc}")
        raise SystemExit(1) from exc
    print(
        "[OK] Preprocessing completed. "
        f"Final points: {result.stats.final_points}. "
        f"Output: {result.stats.output_path}"
    )


if __name__ == "__main__":
    main()

