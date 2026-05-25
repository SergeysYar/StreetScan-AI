"""Urban analytics pipeline orchestrator."""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, field
from pathlib import Path
from time import perf_counter
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import open3d as o3d
import pandas as pd
import yaml

from src.analytics.density_analysis import DensityConfig, compute_density_grid, plot_density_heatmap
from src.analytics.occupancy_grid import OccupancyConfig, build_occupancy_grid, plot_occupancy_map, save_occupancy_csv
from src.analytics.pedestrian_flow import analyze_pedestrian_flow, save_pedestrian_flow
from src.analytics.spatial_statistics import compute_spatial_statistics, save_spatial_statistics
from src.analytics.traffic_analysis import analyze_traffic, save_traffic_summary
from src.analytics.visibility_analysis import VisibilityConfig, compute_visibility_profile, plot_visibility_profile, save_visibility_csv


@dataclass
class AnalyticsConfig:
    """Configuration for analytics pipeline."""

    grid_resolution: float = 0.5
    height_axis: str = "z"
    projection_axes: list[str] = field(default_factory=lambda: ["x", "y"])
    occupancy_threshold: int = 1
    sensor_origin: list[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    max_range: float = 80.0
    visibility_angle_step_deg: float = 1.0
    visibility_range_bins: int = 80
    save_plots: bool = True
    plot_dpi: int = 150
    output_format: str = "png"
    semantic_labels_path: str | None = None
    cluster_stats_path: str | None = None
    trajectory_path: str | None = None
    density_normalization: bool = True
    semantic_vehicle_labels: list[str] = field(default_factory=lambda: ["vehicle"])
    semantic_pedestrian_labels: list[str] = field(default_factory=lambda: ["pedestrian"])


@dataclass
class AnalyticsResult:
    """Output descriptor for analytics pipeline."""

    input_path: str
    output_dir: str
    density_heatmap_path: str | None
    occupancy_grid_path: str | None
    occupancy_map_path: str | None
    spatial_statistics_path: str | None
    traffic_summary_path: str | None
    pedestrian_flow_path: str | None
    visibility_path: str | None
    report_path: str
    processing_time_sec: float
    warnings: list[str]


class UrbanAnalyticsPipeline:
    """Orchestrates spatial analytics modules and output generation."""

    def __init__(self, config: AnalyticsConfig) -> None:
        self.config = config
        self.warnings: list[str] = []
        self._validate_config()

    def _validate_config(self) -> None:
        if self.config.grid_resolution <= 0:
            raise ValueError("grid_resolution must be > 0")
        if self.config.occupancy_threshold <= 0:
            raise ValueError("occupancy_threshold must be > 0")
        if len(self.config.sensor_origin) != 3:
            raise ValueError("sensor_origin must contain exactly 3 values")

    def load_point_cloud(self, input_path: Path) -> np.ndarray:
        """Load supported point cloud and return N x 3 points."""
        if not input_path.exists():
            raise FileNotFoundError(f"Input file does not exist: {input_path}")
        if input_path.suffix.lower() not in {".ply", ".pcd", ".xyz"}:
            raise ValueError(f"Unsupported point cloud extension: {input_path.suffix}")
        cloud = o3d.io.read_point_cloud(str(input_path))
        if cloud.is_empty():
            raise ValueError(f"Input point cloud is empty: {input_path}")
        return np.asarray(cloud.points)

    def load_optional_semantic_labels(self) -> pd.DataFrame | None:
        """Load optional semantic labels CSV."""
        path = self.config.semantic_labels_path
        if path is None:
            return None
        p = Path(path)
        if not p.exists():
            self.warnings.append(f"Semantic labels file not found: {p}")
            return None
        try:
            df = pd.read_csv(p)
        except Exception as exc:
            self.warnings.append(f"Failed to read semantic labels CSV: {exc}")
            return None
        required = {"point_index", "label_id", "label_name"}
        if not required.issubset(df.columns):
            self.warnings.append("Semantic labels CSV missing required columns")
            return None
        return df

    def load_optional_cluster_stats(self) -> pd.DataFrame | None:
        """Load optional cluster statistics CSV."""
        path = self.config.cluster_stats_path
        if path is None:
            return None
        p = Path(path)
        if not p.exists():
            self.warnings.append(f"Cluster stats file not found: {p}")
            return None
        try:
            return pd.read_csv(p)
        except Exception as exc:
            self.warnings.append(f"Failed to read cluster stats CSV: {exc}")
            return None

    def load_optional_trajectories(self) -> pd.DataFrame | None:
        """Load optional trajectory CSV."""
        path = self.config.trajectory_path
        if path is None:
            return None
        p = Path(path)
        if not p.exists():
            self.warnings.append(f"Trajectory file not found: {p}")
            return None
        try:
            return pd.read_csv(p)
        except Exception as exc:
            self.warnings.append(f"Failed to read trajectory CSV: {exc}")
            return None

    def generate_report(self, result: AnalyticsResult, summaries: dict[str, Any], output_path: Path) -> None:
        """Generate analytics markdown report."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            "# Urban Analytics Report",
            "",
            "## 1. Input point cloud",
            f"`{result.input_path}`",
            "",
            "## 2. Available auxiliary data",
            f"- semantic_labels: {'yes' if summaries['semantic_available'] else 'no'}",
            f"- cluster_stats: {'yes' if summaries['cluster_available'] else 'no'}",
            f"- trajectories: {'yes' if summaries['trajectory_available'] else 'no'}",
            "",
            "## 3. Configuration",
            "```yaml",
            yaml.safe_dump({"analytics": asdict(self.config)}, sort_keys=False),
            "```",
            "",
            "## 4. Spatial statistics",
            f"- total_points: {summaries['total_points']} (measured)",
            f"- scene_area_m2: {summaries['scene_area']} (estimated)",
            "",
            "## 5. Density analysis",
            f"- occupied_cells: {summaries['density_occupied']} / {summaries['density_total']} (measured)",
            "",
            "## 6. Occupancy grid summary",
            f"- occupancy_ratio: {summaries['occupancy_ratio']:.4f} (estimated)",
            "",
            "## 7. Traffic analysis",
            f"- source: {summaries['traffic_source']}",
            "",
            "## 8. Pedestrian flow analysis",
            f"- flow_available: {summaries['flow_available']}",
            "",
            "## 9. Visibility analysis",
            f"- angular_coverage_ratio: {summaries['visibility_coverage']:.4f} (estimated)",
            "",
            "## 10. Output files",
            f"- occupancy_grid_csv: `{result.occupancy_grid_path}`",
            f"- spatial_statistics_csv: `{result.spatial_statistics_path}`",
            f"- traffic_summary_csv: `{result.traffic_summary_path}`",
            f"- pedestrian_flow_csv: `{result.pedestrian_flow_path}`",
            f"- visibility_csv: `{result.visibility_path}`",
            f"- density_heatmap_png: `{result.density_heatmap_path}`",
            f"- occupancy_map_png: `{result.occupancy_map_path}`",
            "",
            "## 11. Warnings and limitations",
        ]
        if result.warnings:
            lines.extend([f"- {w}" for w in result.warnings])
        else:
            lines.append("- None")
        lines.append("- Visibility profile is an approximate radial method (not full ray tracing).")
        output_path.write_text("\n".join(lines), encoding="utf-8")

    def run(self, input_path: Path, output_dir: Path) -> AnalyticsResult:
        """Run full analytics pipeline."""
        t0 = perf_counter()
        self.warnings = []
        points = self.load_point_cloud(input_path)
        semantic_df = self.load_optional_semantic_labels()
        cluster_df = self.load_optional_cluster_stats()
        traj_df = self.load_optional_trajectories()

        output_dir.mkdir(parents=True, exist_ok=True)
        plots_dir = Path("outputs/plots/analytics")
        plots_dir.mkdir(parents=True, exist_ok=True)
        report_dir = Path("outputs/reports/analytics")
        report_dir.mkdir(parents=True, exist_ok=True)

        base = input_path.stem
        density_img = plots_dir / f"{base}_density_heatmap.png"
        occupancy_csv = output_dir / f"{base}_occupancy_grid.csv"
        occupancy_img = plots_dir / f"{base}_occupancy_map.png"
        spatial_csv = output_dir / f"{base}_spatial_statistics.csv"
        traffic_csv = output_dir / f"{base}_traffic_summary.csv"
        ped_csv = output_dir / f"{base}_pedestrian_flow.csv"
        vis_csv = output_dir / f"{base}_visibility.csv"
        vis_img = plots_dir / f"{base}_visibility_profile.png"
        report_md = report_dir / f"{base}_analytics_report.md"

        density = compute_density_grid(points, DensityConfig(self.config.grid_resolution, self.config.density_normalization, self.config.plot_dpi))
        occ = build_occupancy_grid(points, OccupancyConfig(self.config.grid_resolution, self.config.occupancy_threshold))
        spatial_df = compute_spatial_statistics(points, semantic_df, cluster_df)

        scene_area_row = spatial_df[spatial_df["metric"] == "scene_area_estimate"]
        scene_area = float(scene_area_row["value"].iloc[0]) if not scene_area_row.empty else 1.0

        traffic_df = analyze_traffic(semantic_df, cluster_df, scene_area, self.config.semantic_vehicle_labels)
        ped_df = analyze_pedestrian_flow(semantic_df, traj_df, scene_area, self.config.semantic_pedestrian_labels)
        vis = compute_visibility_profile(
            points,
            VisibilityConfig(
                sensor_origin=self.config.sensor_origin,
                max_range=self.config.max_range,
                angle_step_deg=self.config.visibility_angle_step_deg,
                range_bins=self.config.visibility_range_bins,
            ),
        )

        save_occupancy_csv(occ, occupancy_csv)
        save_spatial_statistics(spatial_df, spatial_csv)
        save_traffic_summary(traffic_df, traffic_csv)
        save_pedestrian_flow(ped_df, ped_csv)
        save_visibility_csv(vis, vis_csv)

        density_path: str | None = None
        occupancy_map_path: str | None = None
        if self.config.save_plots:
            try:
                plot_density_heatmap(density, density_img, dpi=self.config.plot_dpi)
                density_path = str(density_img)
            except Exception as exc:
                self.warnings.append(f"Density heatmap generation failed: {exc}")
            try:
                plot_occupancy_map(occ, occupancy_img, dpi=self.config.plot_dpi)
                occupancy_map_path = str(occupancy_img)
            except Exception as exc:
                self.warnings.append(f"Occupancy plot generation failed: {exc}")
            try:
                plot_visibility_profile(vis, vis_img, dpi=self.config.plot_dpi)
            except Exception as exc:
                self.warnings.append(f"Visibility plot generation failed: {exc}")
            try:
                self._plot_metric_bar(traffic_df, "Traffic Summary", plots_dir / f"{base}_traffic_summary.png")
            except Exception as exc:
                self.warnings.append(f"Traffic plot generation failed: {exc}")
            try:
                self._plot_metric_bar(ped_df, "Pedestrian Flow", plots_dir / f"{base}_pedestrian_flow.png")
            except Exception as exc:
                self.warnings.append(f"Pedestrian plot generation failed: {exc}")

        result = AnalyticsResult(
            input_path=str(input_path),
            output_dir=str(output_dir),
            density_heatmap_path=density_path,
            occupancy_grid_path=str(occupancy_csv),
            occupancy_map_path=occupancy_map_path,
            spatial_statistics_path=str(spatial_csv),
            traffic_summary_path=str(traffic_csv),
            pedestrian_flow_path=str(ped_csv),
            visibility_path=str(vis_csv),
            report_path=str(report_md),
            processing_time_sec=perf_counter() - t0,
            warnings=list(self.warnings),
        )

        flow_row = ped_df[ped_df["metric"] == "flow_available"]
        flow_available = int(flow_row["value"].iloc[0]) if not flow_row.empty else 0
        summaries = {
            "semantic_available": semantic_df is not None,
            "cluster_available": cluster_df is not None,
            "trajectory_available": traj_df is not None,
            "total_points": int(len(points)),
            "scene_area": scene_area,
            "density_occupied": density.occupied_cells,
            "density_total": density.total_cells,
            "occupancy_ratio": occ.occupancy_ratio,
            "traffic_source": ",".join(sorted(set(traffic_df["source"].astype(str).tolist()))),
            "flow_available": flow_available,
            "visibility_coverage": vis.coverage_ratio,
        }
        self.generate_report(result, summaries, report_md)
        return result

    def _plot_metric_bar(self, df: pd.DataFrame, title: str, path: Path) -> None:
        """Plot numeric metric values as bar chart."""
        d = df.copy()
        d["value_num"] = pd.to_numeric(d["value"], errors="coerce")
        d = d.dropna(subset=["value_num"])
        if d.empty:
            return
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.bar(d["metric"], d["value_num"], color="#2563eb")
        ax.set_title(title)
        ax.set_ylabel("Value")
        ax.tick_params(axis="x", labelrotation=45)
        fig.tight_layout()
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, dpi=self.config.plot_dpi)
        plt.close(fig)


def load_analytics_config(config_path: Path | None) -> AnalyticsConfig:
    """Load analytics config from YAML."""
    if config_path is None:
        return AnalyticsConfig()
    if not config_path.exists():
        raise FileNotFoundError(f"Config file does not exist: {config_path}")
    try:
        raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML config '{config_path}': {exc}") from exc
    section = raw.get("analytics", raw)
    if not isinstance(section, dict):
        raise ValueError(f"Invalid analytics config format in '{config_path}'.")
    return AnalyticsConfig(**section)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="StreetScanAI urban analytics pipeline")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-dir", default="outputs/analytics")
    parser.add_argument("--config", default="configs/analytics.yaml")
    parser.add_argument("--semantic-labels", default=None)
    parser.add_argument("--cluster-stats", default=None)
    parser.add_argument("--trajectories", default=None)
    parser.add_argument("--grid-resolution", type=float, default=None)
    parser.add_argument("--occupancy-threshold", type=int, default=None)
    parser.add_argument("--sensor-origin", nargs=3, type=float, default=None)
    parser.add_argument("--save-plots", action="store_true")
    return parser


def _apply_overrides(cfg: AnalyticsConfig, args: argparse.Namespace) -> AnalyticsConfig:
    merged = AnalyticsConfig(**asdict(cfg))
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
    return merged


def run_from_args(args: argparse.Namespace) -> AnalyticsResult:
    """Execute pipeline from CLI arguments."""
    cfg = load_analytics_config(Path(args.config) if args.config else None)
    cfg = _apply_overrides(cfg, args)
    return UrbanAnalyticsPipeline(cfg).run(Path(args.input), Path(args.output_dir))


def main() -> None:
    """Script entrypoint."""
    parser = _build_parser()
    args = parser.parse_args()
    try:
        result = run_from_args(args)
    except Exception as exc:
        print(f"[ERROR] Analytics pipeline failed: {exc}")
        raise SystemExit(1) from exc
    print(
        "[OK] Analytics completed. "
        f"Report: {result.report_path}. "
        f"Time: {result.processing_time_sec:.3f}s"
    )


if __name__ == "__main__":
    main()
