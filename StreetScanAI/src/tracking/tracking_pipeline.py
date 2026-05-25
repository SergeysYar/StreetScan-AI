"""Main tracking pipeline orchestration and CLI."""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from pathlib import Path
from time import perf_counter

import pandas as pd
import yaml

from src.tracking.trajectory_builder import TrackingConfig, TrajectoryBuilder
from src.tracking.trajectory_smoothing import smooth_all_tracks
from src.tracking.track_visualization import create_trajectory_overlay_cloud, plot_trajectories_xy, plot_velocity_profiles


@dataclass
class TrackingPipelineConfig:
    """Configuration for end-to-end tracking pipeline."""

    fps: float = 10.0
    association_distance_threshold: float = 2.0
    max_missed_frames: int = 5
    min_track_length: int = 3
    enable_kalman_filter: bool = True
    enable_smoothing: bool = True
    smoothing_window: int = 5
    save_overlay_cloud: bool = True
    plot_dpi: int = 150
    velocity_units: str = "m/s"
    default_class_name: str = "unknown"


@dataclass
class TrackingPipelineResult:
    """Output paths and summary info for a pipeline run."""

    input_path: str
    tracked_objects_path: str
    trajectory_summary_path: str
    trajectory_plot_path: str | None
    velocity_plot_path: str | None
    overlay_cloud_path: str | None
    report_path: str
    total_tracks: int
    valid_tracks: int
    processing_time_sec: float
    warnings: list[str]


class TrackingPipeline:
    """Pipeline for trajectory reconstruction, smoothing and export."""

    def __init__(self, config: TrackingPipelineConfig) -> None:
        self.config = config
        self.warnings: list[str] = []
        if config.fps <= 0:
            raise ValueError("fps must be > 0")
        if config.association_distance_threshold <= 0:
            raise ValueError("association_distance_threshold must be > 0")
        if config.smoothing_window <= 0:
            raise ValueError("smoothing_window must be > 0")

    def load_detections(self, input_path: Path) -> pd.DataFrame:
        """Load detection CSV."""
        if not input_path.exists():
            raise FileNotFoundError(f"Input CSV not found: {input_path}")
        df = pd.read_csv(input_path)
        if df.empty:
            raise ValueError("Input CSV is empty")
        return self.normalize_detection_columns(df)

    def normalize_detection_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize multiple CSV schemas to required tracking columns."""
        out = df.copy()
        if "frame_id" not in out.columns:
            raise ValueError("Input CSV must contain frame_id column")
        for col in ["x", "y", "z"]:
            if col not in out.columns:
                raise ValueError(f"Input CSV must contain coordinate column: {col}")
            out[col] = pd.to_numeric(out[col], errors="coerce")
        if out[["x", "y", "z"]].isna().any().any():
            raise ValueError("Coordinates contain non-numeric values")

        out["frame_id"] = pd.to_numeric(out["frame_id"], errors="coerce").astype(int)
        if "timestamp" not in out.columns:
            out["timestamp"] = out["frame_id"].astype(float) / self.config.fps
        else:
            out["timestamp"] = pd.to_numeric(out["timestamp"], errors="coerce")
            out["timestamp"] = out["timestamp"].fillna(out["frame_id"].astype(float) / self.config.fps)

        if "class_name" not in out.columns:
            out["class_name"] = self.config.default_class_name
        else:
            out["class_name"] = out["class_name"].fillna(self.config.default_class_name).astype(str)

        if "confidence" not in out.columns:
            out["confidence"] = pd.NA
        else:
            out["confidence"] = pd.to_numeric(out["confidence"], errors="coerce")

        return out

    def save_tracked_objects(self, df: pd.DataFrame, output_path: Path) -> None:
        """Save tracked objects CSV with required columns."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        cols = [
            "track_id", "frame_id", "timestamp", "class_name", "x", "y", "z",
            "smoothed_x", "smoothed_y", "smoothed_z", "vx", "vy", "vz", "speed", "confidence",
        ]
        for c in cols:
            if c not in df.columns:
                df[c] = pd.NA
        df[cols].to_csv(output_path, index=False)

    def save_summary(self, df: pd.DataFrame, output_path: Path) -> None:
        """Save trajectory summary CSV."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)

    def generate_report(self, result: TrackingPipelineResult, summary_df: pd.DataFrame, output_path: Path) -> None:
        """Generate markdown tracking report."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        top = summary_df.sort_values("path_length", ascending=False).head(10)
        lines = [
            "# Tracking Report",
            "",
            "## 1. Input data",
            f"`{result.input_path}`",
            "",
            "## 2. Tracking configuration",
            "```yaml",
            yaml.safe_dump({"tracking": asdict(self.config)}, sort_keys=False),
            "```",
            "",
            "## 3. Association method",
            "Nearest-neighbor in XYZ with optional Hungarian assignment when scipy is available.",
            "",
            "## 4. Kalman filtering status",
            f"enabled={self.config.enable_kalman_filter}",
            "",
            "## 5. Smoothing status",
            f"enabled={self.config.enable_smoothing}, window={self.config.smoothing_window}",
            "",
            "## 6. Total tracks",
            str(result.total_tracks),
            "",
            "## 7. Valid tracks",
            str(result.valid_tracks),
            "",
            "## 8. Velocity statistics",
            f"mean of mean_speed: {float(summary_df['mean_speed'].mean()) if not summary_df.empty else 0.0:.4f}",
            "",
            "## 9. Longest trajectories",
            "| Track ID | Class | Duration | Points | Mean Speed | Path Length |",
            "|----------|-------|----------|--------|------------|-------------|",
        ]
        for _, r in top.iterrows():
            lines.append(f"| {int(r['track_id'])} | {r['class_name']} | {float(r['duration_sec']):.3f} | {int(r['num_points'])} | {float(r['mean_speed']):.3f} | {float(r['path_length']):.3f} |")
        if top.empty:
            lines.append("| - | - | - | - | - | - |")

        lines.extend(
            [
                "",
                "## 10. Output files",
                f"- tracked_objects_csv: `{result.tracked_objects_path}`",
                f"- trajectory_summary_csv: `{result.trajectory_summary_path}`",
                f"- trajectory_plot: `{result.trajectory_plot_path}`",
                f"- velocity_plot: `{result.velocity_plot_path}`",
                f"- overlay_cloud: `{result.overlay_cloud_path}`",
                "",
                "## 11. Warnings and limitations",
            ]
        )
        if result.warnings:
            lines.extend([f"- {w}" for w in result.warnings])
        else:
            lines.append("- None")
        lines.append("- Association uses Euclidean distance and may fail under severe occlusions.")
        output_path.write_text("\n".join(lines), encoding="utf-8")

    def run(self, input_path: Path, output_dir: Path) -> TrackingPipelineResult:
        """Run end-to-end tracking pipeline."""
        t0 = perf_counter()
        self.warnings = []
        detections = self.load_detections(input_path)

        builder = TrajectoryBuilder(
            TrackingConfig(
                fps=self.config.fps,
                association_distance_threshold=self.config.association_distance_threshold,
                max_missed_frames=self.config.max_missed_frames,
                min_track_length=self.config.min_track_length,
                enable_kalman_filter=self.config.enable_kalman_filter,
                default_class_name=self.config.default_class_name,
            )
        )
        tr = builder.build(detections)
        self.warnings.extend(tr.warnings)

        tracks_df = pd.DataFrame([p.__dict__ for p in tr.track_points])
        if tracks_df.empty:
            raise ValueError("No valid tracks produced (all tracks too short or unmatched).")

        tracks_df["confidence"] = pd.NA
        if self.config.enable_smoothing:
            tracks_df = smooth_all_tracks(tracks_df, self.config.smoothing_window)
        else:
            tracks_df["smoothed_x"] = tracks_df["x"]
            tracks_df["smoothed_y"] = tracks_df["y"]
            tracks_df["smoothed_z"] = tracks_df["z"]

        output_dir.mkdir(parents=True, exist_ok=True)
        plots_dir = Path("outputs/plots/trajectories")
        plots_dir.mkdir(parents=True, exist_ok=True)
        report_dir = Path("outputs/reports/tracking")
        report_dir.mkdir(parents=True, exist_ok=True)

        base = input_path.stem
        tracked_csv = output_dir / f"{base}_tracked_objects.csv"
        summary_csv = output_dir / f"{base}_trajectory_summary.csv"
        traj_plot = plots_dir / f"{base}_trajectories_xy.png"
        vel_plot = plots_dir / f"{base}_velocity.png"
        overlay_ply = output_dir / f"{base}_trajectory_overlay.ply"
        report_md = report_dir / f"{base}_tracking_report.md"

        self.save_tracked_objects(tracks_df, tracked_csv)
        self.save_summary(tr.summary, summary_csv)

        traj_plot_path: str | None = None
        vel_plot_path: str | None = None
        overlay_path: str | None = None

        try:
            plot_trajectories_xy(tracks_df, traj_plot, dpi=self.config.plot_dpi)
            traj_plot_path = str(traj_plot)
        except Exception as exc:
            self.warnings.append(f"Trajectory plot generation failed: {exc}")
        try:
            plot_velocity_profiles(tracks_df, vel_plot, dpi=self.config.plot_dpi)
            vel_plot_path = str(vel_plot)
        except Exception as exc:
            self.warnings.append(f"Velocity plot generation failed: {exc}")

        if self.config.save_overlay_cloud:
            try:
                create_trajectory_overlay_cloud(tracks_df, overlay_ply)
                overlay_path = str(overlay_ply)
            except Exception as exc:
                self.warnings.append(f"Overlay cloud export failed: {exc}")

        result = TrackingPipelineResult(
            input_path=str(input_path),
            tracked_objects_path=str(tracked_csv),
            trajectory_summary_path=str(summary_csv),
            trajectory_plot_path=traj_plot_path,
            velocity_plot_path=vel_plot_path,
            overlay_cloud_path=overlay_path,
            report_path=str(report_md),
            total_tracks=tr.total_tracks,
            valid_tracks=tr.valid_tracks,
            processing_time_sec=perf_counter() - t0,
            warnings=list(self.warnings),
        )
        self.generate_report(result, tr.summary, report_md)
        return result


def load_tracking_config(config_path: Path | None) -> TrackingPipelineConfig:
    """Load tracking configuration from YAML."""
    if config_path is None:
        return TrackingPipelineConfig()
    if not config_path.exists():
        raise FileNotFoundError(f"Config file does not exist: {config_path}")
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    section = raw.get("tracking", raw)
    if not isinstance(section, dict):
        raise ValueError(f"Invalid tracking config format in '{config_path}'.")
    return TrackingPipelineConfig(**section)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="StreetScanAI tracking pipeline")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-dir", default="outputs/trajectories")
    parser.add_argument("--config", default="configs/tracking.yaml")
    parser.add_argument("--fps", type=float, default=None)
    parser.add_argument("--association-distance", type=float, default=None)
    parser.add_argument("--max-missed-frames", type=int, default=None)
    parser.add_argument("--min-track-length", type=int, default=None)
    parser.add_argument("--no-kalman", action="store_true")
    parser.add_argument("--no-smoothing", action="store_true")
    parser.add_argument("--smoothing-window", type=int, default=None)
    parser.add_argument("--save-overlay-cloud", action="store_true")
    return parser


def _apply_overrides(cfg: TrackingPipelineConfig, args: argparse.Namespace) -> TrackingPipelineConfig:
    merged = TrackingPipelineConfig(**asdict(cfg))
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
    return merged


def run_from_args(args: argparse.Namespace) -> TrackingPipelineResult:
    """Run pipeline from argparse namespace."""
    cfg = load_tracking_config(Path(args.config) if args.config else None)
    cfg = _apply_overrides(cfg, args)
    return TrackingPipeline(cfg).run(Path(args.input), Path(args.output_dir))


def main() -> None:
    """Direct script entrypoint."""
    parser = _build_parser()
    args = parser.parse_args()
    try:
        result = run_from_args(args)
    except Exception as exc:
        print(f"[ERROR] Tracking pipeline failed: {exc}")
        raise SystemExit(1) from exc
    print(
        "[OK] Tracking completed. "
        f"Valid tracks: {result.valid_tracks}. "
        f"Report: {result.report_path}"
    )


if __name__ == "__main__":
    main()
