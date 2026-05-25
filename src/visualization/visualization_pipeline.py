"""Main visualization orchestration pipeline for StreetScanAI."""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from src.visualization.animation_exporter import export_turntable_gif
from src.visualization.birdeye_renderer import render_bird_eye_view
from src.visualization.cluster_renderer import load_cluster_labels, render_cluster_cloud
from src.visualization.heatmap_renderer import (
    render_density_heatmap_from_csv,
    render_density_heatmap_from_points,
    render_occupancy_map_from_csv,
)
from src.visualization.pointcloud_viewer import ViewerConfig, load_cloud, open_interactive_viewer, render_pointcloud
from src.visualization.semantic_renderer import load_semantic_labels, render_semantic_cloud
from src.visualization.trajectory_renderer import load_trajectories, plot_trajectories_2d, render_trajectory_overlay


@dataclass
class VisualizationConfig:
    """Configuration for visualization pipeline."""

    backend: str = "open3d"
    image_width: int = 1600
    image_height: int = 1000
    point_size: float = 2.0
    background_color: list[float] = field(default_factory=lambda: [1.0, 1.0, 1.0])
    camera_view: str = "isometric"
    save_screenshot: bool = True
    save_animation: bool = False
    animation_frames: int = 60
    animation_fps: int = 20
    bird_eye_resolution: float = 0.2
    plot_dpi: int = 150
    show_axes: bool = True
    show_legend: bool = True
    semantic_labels_path: str | None = None
    cluster_labels_path: str | None = None
    density_grid_path: str | None = None
    occupancy_grid_path: str | None = None
    trajectories_path: str | None = None
    interactive: bool = False


@dataclass
class VisualizationResult:
    """Output artifacts summary for visualization run."""

    input_path: str
    output_dir: str
    pointcloud_screenshot: str | None
    semantic_screenshot: str | None
    cluster_screenshot: str | None
    bird_eye_image: str | None
    heatmap_image: str | None
    trajectory_image: str | None
    animation_path: str | None
    report_path: str
    warnings: list[str]


class VisualizationPipeline:
    """Runs all selected visualization steps and exports report."""

    def __init__(self, config: VisualizationConfig) -> None:
        self.config = config
        self.warnings: list[str] = []

    def _viewer_cfg(self) -> ViewerConfig:
        return ViewerConfig(
            backend=self.config.backend,
            image_width=self.config.image_width,
            image_height=self.config.image_height,
            point_size=self.config.point_size,
            background_color=tuple(float(v) for v in self.config.background_color),
            camera_view=self.config.camera_view,
            show_axes=self.config.show_axes,
            save_screenshot=self.config.save_screenshot,
            interactive=self.config.interactive,
        )

    def run(self, input_path: Path, output_dir: Path) -> VisualizationResult:
        """Execute visualization pipeline."""
        output_dir.mkdir(parents=True, exist_ok=True)
        report_dir = Path("outputs/reports/visualization")
        report_dir.mkdir(parents=True, exist_ok=True)
        base = input_path.stem

        pointcloud_png = output_dir / f"{base}_pointcloud.png"
        semantic_png = output_dir / f"{base}_semantic.png"
        cluster_png = output_dir / f"{base}_clusters.png"
        bird_png = output_dir / f"{base}_bird_eye.png"
        heatmap_png = output_dir / f"{base}_density_heatmap.png"
        traj_png = output_dir / f"{base}_trajectories.png"
        gif_path = output_dir / f"{base}_turntable.gif"
        report_md = report_dir / f"{base}_visualization_report.md"

        pointcloud_path: str | None = None
        semantic_path: str | None = None
        cluster_path: str | None = None
        bird_path: str | None = None
        heatmap_path: str | None = None
        trajectory_path: str | None = None
        animation_path: str | None = None

        cloud = load_cloud(input_path)
        pts = np.asarray(cloud.points)
        vcfg = self._viewer_cfg()

        try:
            if self.config.save_screenshot:
                render_pointcloud(cloud, pointcloud_png, vcfg)
                pointcloud_path = str(pointcloud_png)
            if self.config.interactive:
                open_interactive_viewer(cloud, vcfg)
        except Exception as exc:
            self.warnings.append(f"Point cloud rendering failed: {exc}")

        try:
            if self.config.semantic_labels_path:
                sem_df = load_semantic_labels(Path(self.config.semantic_labels_path))
                if len(sem_df) == len(pts):
                    render_semantic_cloud(input_path, Path(self.config.semantic_labels_path), semantic_png, vcfg)
                    semantic_path = str(semantic_png)
                else:
                    self.warnings.append("Semantic labels count does not match point count; semantic rendering skipped.")
        except Exception as exc:
            self.warnings.append(f"Semantic rendering failed: {exc}")

        try:
            if self.config.cluster_labels_path:
                clu_df = load_cluster_labels(Path(self.config.cluster_labels_path))
                if len(clu_df) == len(pts):
                    render_cluster_cloud(input_path, Path(self.config.cluster_labels_path), cluster_png, vcfg)
                    cluster_path = str(cluster_png)
                else:
                    self.warnings.append("Cluster labels count does not match point count; cluster rendering skipped.")
        except Exception as exc:
            self.warnings.append(f"Cluster rendering failed: {exc}")

        try:
            render_bird_eye_view(input_path, bird_png, self.config.bird_eye_resolution, self.config.plot_dpi)
            bird_path = str(bird_png)
        except Exception as exc:
            self.warnings.append(f"Bird-eye rendering failed: {exc}")

        try:
            if self.config.density_grid_path:
                render_density_heatmap_from_csv(Path(self.config.density_grid_path), heatmap_png, self.config.plot_dpi)
            else:
                render_density_heatmap_from_points(pts, heatmap_png, self.config.bird_eye_resolution, self.config.plot_dpi)
            heatmap_path = str(heatmap_png)
        except Exception as exc:
            self.warnings.append(f"Density heatmap rendering failed: {exc}")

        try:
            if self.config.occupancy_grid_path:
                occ_png = output_dir / f"{base}_occupancy_map.png"
                render_occupancy_map_from_csv(Path(self.config.occupancy_grid_path), occ_png, self.config.plot_dpi)
        except Exception as exc:
            self.warnings.append(f"Occupancy map rendering failed: {exc}")

        try:
            if self.config.trajectories_path:
                tdf = load_trajectories(Path(self.config.trajectories_path))
                plot_trajectories_2d(tdf, traj_png, self.config.plot_dpi)
                trajectory_path = str(traj_png)
                if pointcloud_path is None:
                    overlay = output_dir / f"{base}_trajectory_overlay.png"
                    render_trajectory_overlay(input_path, Path(self.config.trajectories_path), overlay, vcfg)
        except Exception as exc:
            self.warnings.append(f"Trajectory rendering failed: {exc}")

        try:
            if self.config.save_animation:
                export_turntable_gif(input_path, gif_path, self.config)
                animation_path = str(gif_path)
        except Exception as exc:
            self.warnings.append(f"Animation export failed: {exc}")

        result = VisualizationResult(
            input_path=str(input_path),
            output_dir=str(output_dir),
            pointcloud_screenshot=pointcloud_path,
            semantic_screenshot=semantic_path,
            cluster_screenshot=cluster_path,
            bird_eye_image=bird_path,
            heatmap_image=heatmap_path,
            trajectory_image=trajectory_path,
            animation_path=animation_path,
            report_path=str(report_md),
            warnings=list(self.warnings),
        )
        self.generate_report(result, report_md)
        return result

    def generate_report(self, result: VisualizationResult, output_path: Path) -> None:
        """Generate markdown visualization report."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            "# Visualization Report",
            "",
            "## 1. Input point cloud",
            f"`{result.input_path}`",
            "",
            "## 2. Visualization configuration",
            "```yaml",
            yaml.safe_dump({"visualization": asdict(self.config)}, sort_keys=False),
            "```",
            "",
            "## 3. Generated visual outputs",
            f"- pointcloud: `{result.pointcloud_screenshot}`",
            f"- semantic: `{result.semantic_screenshot}`",
            f"- clusters: `{result.cluster_screenshot}`",
            f"- bird_eye: `{result.bird_eye_image}`",
            f"- density_heatmap: `{result.heatmap_image}`",
            f"- trajectories: `{result.trajectory_image}`",
            "",
            "## 4. Optional semantic visualization",
            "Generated only when semantic labels are provided and aligned by point count.",
            "",
            "## 5. Optional cluster visualization",
            "Generated only when cluster labels are provided and aligned by point count.",
            "",
            "## 6. Optional trajectory visualization",
            "Generated only when trajectory CSV is provided.",
            "",
            "## 7. Optional heatmap outputs",
            "Density map always attempted; occupancy map optional from occupancy grid CSV.",
            "",
            "## 8. Animation export status",
            f"`{result.animation_path}`",
            "",
            "## 9. Output file paths",
            f"- output_dir: `{result.output_dir}`",
            f"- report: `{result.report_path}`",
            "",
            "## 10. Warnings and limitations",
        ]
        if result.warnings:
            lines.extend([f"- {w}" for w in result.warnings])
        else:
            lines.append("- None")
        lines.append("- In headless environments, some off-screen backends may fail; pipeline continues with warnings.")
        output_path.write_text("\n".join(lines), encoding="utf-8")


def load_visualization_config(config_path: Path | None) -> VisualizationConfig:
    """Load visualization configuration from YAML."""
    if config_path is None:
        return VisualizationConfig()
    if not config_path.exists():
        raise FileNotFoundError(f"Config file does not exist: {config_path}")
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    section = raw.get("visualization", raw)
    if not isinstance(section, dict):
        raise ValueError(f"Invalid visualization config format in '{config_path}'.")
    return VisualizationConfig(**section)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="StreetScanAI visualization pipeline")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-dir", default="outputs/visualizations")
    parser.add_argument("--config", default="configs/visualization.yaml")
    parser.add_argument("--semantic-labels", default=None)
    parser.add_argument("--cluster-labels", default=None)
    parser.add_argument("--density-grid", default=None)
    parser.add_argument("--occupancy-grid", default=None)
    parser.add_argument("--trajectories", default=None)
    parser.add_argument("--backend", choices=["open3d", "pyvista"], default=None)
    parser.add_argument("--camera-view", choices=["isometric", "top", "front", "side"], default=None)
    parser.add_argument("--save-animation", action="store_true")
    parser.add_argument("--interactive", action="store_true")
    return parser


def _apply_overrides(cfg: VisualizationConfig, args: argparse.Namespace) -> VisualizationConfig:
    merged = VisualizationConfig(**asdict(cfg))
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
    return merged


def run_from_args(args: argparse.Namespace) -> VisualizationResult:
    """Run visualization from CLI args."""
    cfg = load_visualization_config(Path(args.config) if args.config else None)
    cfg = _apply_overrides(cfg, args)
    return VisualizationPipeline(cfg).run(Path(args.input), Path(args.output_dir))


def main() -> None:
    """Direct script entrypoint."""
    parser = _build_parser()
    args = parser.parse_args()
    try:
        result = run_from_args(args)
    except Exception as exc:
        print(f"[ERROR] Visualization pipeline failed: {exc}")
        raise SystemExit(1) from exc
    print(f"[OK] Visualization completed. Report: {result.report_path}")


if __name__ == "__main__":
    main()
