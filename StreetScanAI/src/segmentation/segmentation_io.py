"""I/O helpers for semantic segmentation subsystem."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import open3d as o3d
import pandas as pd

from src.segmentation.labels import get_label_name


def load_point_cloud(path: Path) -> o3d.geometry.PointCloud:
    """Load point cloud from supported format."""
    if not path.exists():
        raise FileNotFoundError(f"Input file does not exist: {path}")
    if path.suffix.lower() not in {".ply", ".pcd", ".xyz"}:
        raise ValueError(f"Unsupported point cloud extension: {path.suffix}")
    try:
        cloud = o3d.io.read_point_cloud(str(path))
    except Exception as exc:
        raise RuntimeError(f"Failed to read point cloud '{path}': {exc}") from exc
    if cloud.is_empty() or len(np.asarray(cloud.points)) == 0:
        raise ValueError(f"Point cloud is empty: {path}")
    return cloud


def save_point_cloud(cloud: o3d.geometry.PointCloud, path: Path) -> None:
    """Save point cloud to disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        ok = o3d.io.write_point_cloud(str(path), cloud)
    except Exception as exc:
        raise RuntimeError(f"Failed to write point cloud '{path}': {exc}") from exc
    if not ok:
        raise RuntimeError(f"Open3D failed to write point cloud: {path}")


def save_labels_csv(
    points: np.ndarray,
    labels: np.ndarray,
    output_path: Path,
    confidence: np.ndarray | None = None,
) -> None:
    """Save per-point semantic labels CSV."""
    if len(points) != len(labels):
        raise ValueError("Label count does not match number of points.")
    if confidence is not None and len(confidence) != len(labels):
        raise ValueError("Confidence length does not match number of labels.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(
        {
            "point_index": np.arange(len(points), dtype=int),
            "x": points[:, 0],
            "y": points[:, 1],
            "z": points[:, 2],
            "label_id": labels.astype(int),
            "label_name": [get_label_name(int(v)) for v in labels],
            "confidence": confidence if confidence is not None else np.full(len(labels), np.nan),
        }
    )
    df.to_csv(output_path, index=False)


def load_labels_csv(path: Path) -> np.ndarray:
    """Load optional labels from CSV format."""
    if not path.exists():
        raise FileNotFoundError(f"Labels file does not exist: {path}")
    df = pd.read_csv(path)
    required = {"point_index", "label_id"}
    if not required.issubset(df.columns):
        raise ValueError(f"Labels CSV must contain columns: {sorted(required)}")
    return df.sort_values("point_index")["label_id"].to_numpy(dtype=int)


def save_stats_csv(stats: dict[str, int], output_path: Path) -> None:
    """Save semantic class counts to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rows = [{"class": k, "points": int(v)} for k, v in stats.items()]
    pd.DataFrame(rows).to_csv(output_path, index=False)


def save_report_markdown(result: Any, stats: dict[str, int], output_path: Path) -> None:
    """Save semantic segmentation report."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    total = max(1, int(result.total_points))
    lines = [
        "# Semantic Segmentation Report",
        "",
        "## 1. Input cloud",
        f"`{result.input_path}`",
        "",
        "## 2. Segmentation method",
        f"`{result.method}`",
        "",
        "## 3. Semantic classes",
        "unlabeled, road, building, vehicle, pedestrian, vegetation, pole, traffic_sign",
        "",
        "## 4. Configuration",
        "See active config and CLI overrides used during execution.",
        "",
        "## 5. Total points",
        str(result.total_points),
        "",
        "## 6. Class distribution table",
        "| Class | Label ID | Points | Share |",
        "|-------|----------|--------|-------|",
    ]
    label_order = ["unlabeled", "road", "building", "vehicle", "pedestrian", "vegetation", "pole", "traffic_sign"]
    label_id_map = {name: idx for idx, name in enumerate(label_order)}
    for name in label_order:
        pts = int(stats.get(name, 0))
        lines.append(f"| {name} | {label_id_map[name]} | {pts} | {pts / total:.4f} |")

    lines.extend(
        [
            "",
            "## 7. Output files",
            f"- Semantic cloud: `{result.output_cloud_path}`",
            f"- Labels CSV: `{result.labels_path}`",
            f"- Stats CSV: `{result.stats_path}`",
            f"- Report: `{result.report_path}`",
            f"- Screenshot: `{result.screenshot_path or 'not generated'}`",
            "",
            "## 8. Warnings",
        ]
    )
    if result.warnings:
        lines.extend([f"- {w}" for w in result.warnings])
    else:
        lines.append("- None")

    lines.extend(
        [
            "",
            "## 9. Limitations",
            "- Baseline mode is rule-based and deterministic, but not a learned model.",
            "- PointNet++ mode requires valid trained weights and implementation integration.",
        ]
    )
    output_path.write_text("\n".join(lines), encoding="utf-8")
