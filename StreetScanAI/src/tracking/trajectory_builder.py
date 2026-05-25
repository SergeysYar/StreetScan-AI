"""Trajectory reconstruction and ID assignment from detections."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from src.tracking.kalman_tracker import KalmanConfig, KalmanTrack, KalmanTracker
from src.tracking.velocity_estimation import estimate_velocity_from_points

try:
    from scipy.optimize import linear_sum_assignment
except Exception:  # pragma: no cover
    linear_sum_assignment = None


@dataclass
class TrackingConfig:
    """Configuration for trajectory construction."""

    fps: float = 10.0
    association_distance_threshold: float = 2.0
    max_missed_frames: int = 5
    min_track_length: int = 3
    enable_kalman_filter: bool = True
    default_class_name: str = "unknown"


@dataclass
class DetectionRecord:
    """One frame-level detection record."""

    frame_id: int
    timestamp: float
    x: float
    y: float
    z: float
    class_name: str
    confidence: float | None


@dataclass
class TrackPoint:
    """One point in a reconstructed trajectory."""

    track_id: int
    frame_id: int
    timestamp: float
    x: float
    y: float
    z: float
    vx: float | None
    vy: float | None
    vz: float | None
    speed: float | None
    class_name: str


@dataclass
class TrajectoryResult:
    """Trajectory reconstruction output."""

    track_points: list[TrackPoint]
    summary: pd.DataFrame
    total_tracks: int
    valid_tracks: int
    dropped_tracks: int
    warnings: list[str]


class TrajectoryBuilder:
    """Builds multi-frame trajectories from centroid detections."""

    def __init__(self, config: TrackingConfig) -> None:
        self.config = config
        if config.fps <= 0:
            raise ValueError("fps must be > 0")
        if config.association_distance_threshold <= 0:
            raise ValueError("association_distance_threshold must be > 0")
        self.kalman = KalmanTracker(KalmanConfig(dt=1.0 / config.fps)) if config.enable_kalman_filter else None

    def build_from_csv(self, input_path: Path) -> TrajectoryResult:
        """Load detections CSV and build trajectories."""
        if not input_path.exists():
            raise FileNotFoundError(f"Input detection CSV does not exist: {input_path}")
        df = pd.read_csv(input_path)
        return self.build(df)

    def build(self, detections: pd.DataFrame) -> TrajectoryResult:
        """Build trajectories from normalized detection dataframe."""
        if detections.empty:
            raise ValueError("Input detections dataframe is empty.")
        required = {"frame_id", "x", "y", "z"}
        if not required.issubset(detections.columns):
            raise ValueError(f"Missing required detection columns: {sorted(required)}")

        df = detections.copy()
        if "timestamp" not in df.columns:
            df["timestamp"] = df["frame_id"].astype(float) / self.config.fps
        if "class_name" not in df.columns:
            df["class_name"] = self.config.default_class_name
        if "confidence" not in df.columns:
            df["confidence"] = np.nan

        df = df.sort_values(["frame_id"]).reset_index(drop=True)

        active_tracks: dict[int, KalmanTrack] = {}
        history: list[dict[str, float | int | str | None]] = []
        next_id = 1
        warnings: list[str] = []

        for frame_id, grp in df.groupby("frame_id", sort=True):
            detections_xyz = grp[["x", "y", "z"]].to_numpy(dtype=float)
            det_meta = grp[["timestamp", "class_name", "confidence"]].reset_index(drop=True)

            for tid in list(active_tracks.keys()):
                if self.kalman is not None:
                    active_tracks[tid] = self.kalman.predict(active_tracks[tid])
                else:
                    active_tracks[tid].missed_frames += 1
                    active_tracks[tid].age += 1

            assignments, unmatched_tracks, unmatched_det = self.assign_detections_to_tracks(active_tracks, detections_xyz)

            self.update_existing_tracks(active_tracks, assignments, detections_xyz, det_meta)

            for tid in unmatched_tracks:
                if tid in active_tracks:
                    active_tracks[tid].missed_frames += 1

            created = self.create_new_tracks(unmatched_det, detections_xyz, det_meta, next_id)
            for tr in created:
                active_tracks[tr.track_id] = tr
                next_id = max(next_id, tr.track_id + 1)

            self.remove_stale_tracks(active_tracks)

            for tid, tr in active_tracks.items():
                pos = self.kalman.get_position(tr) if self.kalman is not None else tr.state[:3]
                history.append(
                    {
                        "track_id": int(tid),
                        "frame_id": int(frame_id),
                        "timestamp": float(det_meta["timestamp"].iloc[0]) if len(det_meta) > 0 else float(frame_id) / self.config.fps,
                        "x": float(pos[0]),
                        "y": float(pos[1]),
                        "z": float(pos[2]),
                        "class_name": str(tr.class_name),
                        "confidence": float(tr.confidence) if tr.confidence is not None and np.isfinite(tr.confidence) else np.nan,
                    }
                )

        tracks_df = pd.DataFrame(history).drop_duplicates(subset=["track_id", "frame_id"], keep="last")
        if tracks_df.empty:
            warnings.append("No tracks reconstructed from input detections.")
            return TrajectoryResult([], pd.DataFrame(), 0, 0, 0, warnings)

        tracks_df = estimate_velocity_from_points(tracks_df, self.config.fps)
        summary = self.summarize_tracks(tracks_df)
        valid_ids = set(summary[summary["num_points"] >= self.config.min_track_length]["track_id"].tolist())
        final_df = tracks_df[tracks_df["track_id"].isin(valid_ids)].copy()
        dropped = int(summary.shape[0] - len(valid_ids))

        points = [
            TrackPoint(
                track_id=int(r.track_id), frame_id=int(r.frame_id), timestamp=float(r.timestamp), x=float(r.x), y=float(r.y), z=float(r.z),
                vx=float(r.vx) if pd.notna(r.vx) else None, vy=float(r.vy) if pd.notna(r.vy) else None, vz=float(r.vz) if pd.notna(r.vz) else None,
                speed=float(r.speed) if pd.notna(r.speed) else None, class_name=str(r.class_name)
            )
            for r in final_df.itertuples(index=False)
        ]
        return TrajectoryResult(points, summary, int(summary.shape[0]), int(len(valid_ids)), dropped, warnings)

    def assign_detections_to_tracks(self, active_tracks: dict[int, KalmanTrack], detections_xyz: np.ndarray) -> tuple[list[tuple[int, int]], list[int], list[int]]:
        """Associate detections with tracks by nearest-neighbor/Hungarian."""
        track_ids = list(active_tracks.keys())
        if len(track_ids) == 0:
            return [], [], list(range(len(detections_xyz)))
        if len(detections_xyz) == 0:
            return [], track_ids, []

        track_pos = np.array([(self.kalman.get_position(active_tracks[tid]) if self.kalman is not None else active_tracks[tid].state[:3]) for tid in track_ids])
        dmat = np.linalg.norm(track_pos[:, None, :] - detections_xyz[None, :, :], axis=2)

        assignments: list[tuple[int, int]] = []
        if linear_sum_assignment is not None:
            ri, ci = linear_sum_assignment(dmat)
            for r, c in zip(ri.tolist(), ci.tolist()):
                if dmat[r, c] <= self.config.association_distance_threshold:
                    assignments.append((track_ids[r], int(c)))
        else:
            used_tracks: set[int] = set()
            used_det: set[int] = set()
            flat = [(i, j, dmat[i, j]) for i in range(dmat.shape[0]) for j in range(dmat.shape[1])]
            flat.sort(key=lambda x: x[2])
            for i, j, dist in flat:
                tid = track_ids[i]
                if dist > self.config.association_distance_threshold:
                    break
                if tid in used_tracks or j in used_det:
                    continue
                assignments.append((tid, j))
                used_tracks.add(tid)
                used_det.add(j)

        assigned_tracks = {tid for tid, _ in assignments}
        assigned_det = {d for _, d in assignments}
        unmatched_tracks = [tid for tid in track_ids if tid not in assigned_tracks]
        unmatched_det = [i for i in range(len(detections_xyz)) if i not in assigned_det]
        return assignments, unmatched_tracks, unmatched_det

    def create_new_tracks(self, unmatched_det: list[int], detections_xyz: np.ndarray, det_meta: pd.DataFrame, next_id: int) -> list[KalmanTrack]:
        """Create tracks from unmatched detections."""
        out: list[KalmanTrack] = []
        current = next_id
        for di in unmatched_det:
            cls = str(det_meta.loc[di, "class_name"]) if "class_name" in det_meta.columns else self.config.default_class_name
            conf = det_meta.loc[di, "confidence"] if "confidence" in det_meta.columns else np.nan
            if self.kalman is not None:
                tr = self.kalman.initialize_track(detections_xyz[di], current, cls)
            else:
                st = np.zeros(6, dtype=float)
                st[:3] = detections_xyz[di]
                tr = KalmanTrack(track_id=current, state=st, covariance=np.eye(6), age=1, missed_frames=0, class_name=cls, confidence=None)
            tr.confidence = float(conf) if pd.notna(conf) else None
            out.append(tr)
            current += 1
        return out

    def update_existing_tracks(self, active_tracks: dict[int, KalmanTrack], assignments: list[tuple[int, int]], detections_xyz: np.ndarray, det_meta: pd.DataFrame) -> None:
        """Update matched tracks with associated detections."""
        for tid, di in assignments:
            tr = active_tracks[tid]
            if self.kalman is not None:
                tr = self.kalman.update(tr, detections_xyz[di])
            else:
                tr.state[:3] = detections_xyz[di]
                tr.missed_frames = 0
            tr.class_name = str(det_meta.loc[di, "class_name"]) if "class_name" in det_meta.columns else tr.class_name
            conf = det_meta.loc[di, "confidence"] if "confidence" in det_meta.columns else np.nan
            tr.confidence = float(conf) if pd.notna(conf) else tr.confidence
            active_tracks[tid] = tr

    def remove_stale_tracks(self, active_tracks: dict[int, KalmanTrack]) -> None:
        """Remove tracks that exceeded max_missed_frames."""
        stale = [tid for tid, tr in active_tracks.items() if tr.missed_frames > self.config.max_missed_frames]
        for tid in stale:
            del active_tracks[tid]

    def finalize_tracks(self, tracks_df: pd.DataFrame) -> pd.DataFrame:
        """Finalize track dataframe placeholder for extension."""
        return tracks_df.sort_values(["track_id", "frame_id"]).reset_index(drop=True)

    def summarize_tracks(self, tracks_df: pd.DataFrame) -> pd.DataFrame:
        """Build per-track summary dataframe."""
        rows = []
        for tid, grp in tracks_df.groupby("track_id", sort=False):
            grp = grp.sort_values("frame_id")
            dt = float(grp["timestamp"].iloc[-1] - grp["timestamp"].iloc[0]) if len(grp) > 1 else 0.0
            dif = np.diff(grp[["x", "y", "z"]].to_numpy(dtype=float), axis=0)
            path = float(np.linalg.norm(dif, axis=1).sum()) if len(dif) > 0 else 0.0
            rows.append(
                {
                    "track_id": int(tid),
                    "class_name": str(grp["class_name"].mode().iloc[0]) if "class_name" in grp.columns else "unknown",
                    "start_frame": int(grp["frame_id"].min()),
                    "end_frame": int(grp["frame_id"].max()),
                    "duration_sec": dt,
                    "num_points": int(len(grp)),
                    "path_length": path,
                    "mean_speed": float(pd.to_numeric(grp["speed"], errors="coerce").fillna(0.0).mean()) if "speed" in grp.columns else 0.0,
                    "max_speed": float(pd.to_numeric(grp["speed"], errors="coerce").fillna(0.0).max()) if "speed" in grp.columns else 0.0,
                    "min_x": float(grp["x"].min()),
                    "min_y": float(grp["y"].min()),
                    "min_z": float(grp["z"].min()),
                    "max_x": float(grp["x"].max()),
                    "max_y": float(grp["y"].max()),
                    "max_z": float(grp["z"].max()),
                }
            )
        return pd.DataFrame(rows)


def build_trajectories(frame_cluster_df: pd.DataFrame) -> pd.DataFrame:
    """Backward-compatible helper retained for legacy usage."""
    trajectory = frame_cluster_df.copy()
    if "cluster_id" in trajectory.columns:
        trajectory["object_id"] = trajectory["cluster_id"]
    return trajectory
