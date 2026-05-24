"""Object clustering subsystem for urban LiDAR point clouds.

Implements DBSCAN and Euclidean-style clustering with:
- deterministic cluster coloring
- per-cluster statistics and bounding boxes
- labels/statistics export
- Markdown report generation
- optional screenshot export
"""
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
from sklearn.neighbors import NearestNeighbors


@dataclass
class ClusteringConfig:
    """Configuration for point cloud clustering."""

    method: str = "dbscan"
    eps: float = 0.8
    min_points: int = 20
    euclidean_tolerance: float = 0.6
    min_cluster_size: int = 30
    max_cluster_size: int | None = None
    remove_noise: bool = True
    color_noise_gray: bool = True
    compute_bounding_boxes: bool = True
    compute_oriented_bounding_boxes: bool = False
    save_screenshot: bool = False
    random_seed: int = 42


@dataclass
class ClusterInfo:
    """Statistics for a single cluster."""

    cluster_id: int
    label: int
    point_count: int
    centroid: list[float]
    bbox_min: list[float]
    bbox_max: list[float]
    bbox_extent: list[float]
    bbox_volume: float
    density: float | None
    is_noise: bool


@dataclass
class ClusteringResult:
    """Result object of a clustering run."""

    labels: np.ndarray
    clustered_cloud: o3d.geometry.PointCloud
    cluster_infos: list[ClusterInfo]
    noise_points: int
    valid_clusters: int
    processing_time_sec: float
    output_paths: dict[str, str]
    warnings: list[str] = field(default_factory=list)


class PointCloudClusterer:
    """Reusable clusterer for urban LiDAR point clouds."""

    def __init__(self, config: ClusteringConfig) -> None:
        self.config = config
        self._obb_info: dict[int, dict[str, Any]] = {}
        self._validate_config()

    def _validate_config(self) -> None:
        if self.config.method not in {"dbscan", "euclidean"}:
            raise ValueError("method must be 'dbscan' or 'euclidean'")
        if self.config.eps <= 0:
            raise ValueError("eps must be > 0")
        if self.config.min_points <= 0:
            raise ValueError("min_points must be > 0")
        if self.config.euclidean_tolerance <= 0:
            raise ValueError("euclidean_tolerance must be > 0")
        if self.config.min_cluster_size <= 0:
            raise ValueError("min_cluster_size must be > 0")
        if self.config.max_cluster_size is not None and self.config.max_cluster_size < self.config.min_cluster_size:
            raise ValueError("max_cluster_size must be >= min_cluster_size")

    def load_point_cloud(self, input_path: Path) -> o3d.geometry.PointCloud:
        """Load .ply/.pcd/.xyz point cloud from disk."""
        if not input_path.exists():
            raise FileNotFoundError(f"Input file does not exist: {input_path}")
        if input_path.suffix.lower() not in {".ply", ".pcd", ".xyz"}:
            raise ValueError(f"Unsupported file extension: {input_path.suffix}")
        try:
            cloud = o3d.io.read_point_cloud(str(input_path))
        except Exception as exc:
            raise RuntimeError(f"Failed to read point cloud '{input_path}': {exc}") from exc
        if cloud.is_empty() or len(np.asarray(cloud.points)) == 0:
            raise ValueError(f"Input point cloud is empty: {input_path}")
        return cloud

    def run_dbscan(self, cloud: o3d.geometry.PointCloud) -> np.ndarray:
        """Run Open3D DBSCAN."""
        labels = np.asarray(
            cloud.cluster_dbscan(
                eps=self.config.eps,
                min_points=self.config.min_points,
                print_progress=True,
            ),
            dtype=int,
        )
        return labels

    def run_euclidean_clustering(self, cloud: o3d.geometry.PointCloud) -> np.ndarray:
        """Run Euclidean-style clustering with radius-based BFS."""
        points = np.asarray(cloud.points)
        n = len(points)
        labels = np.full(n, -1, dtype=int)
        if n == 0:
            return labels

        nn = NearestNeighbors(radius=self.config.euclidean_tolerance)
        nn.fit(points)
        neighborhoods = nn.radius_neighbors(points, return_distance=False)

        visited = np.zeros(n, dtype=bool)
        current_label = 0
        for i in range(n):
            if visited[i]:
                continue
            visited[i] = True
            queue = [i]
            component: list[int] = []
            while queue:
                idx = queue.pop()
                component.append(idx)
                for nb in neighborhoods[idx]:
                    if not visited[nb]:
                        visited[nb] = True
                        queue.append(int(nb))

            csize = len(component)
            if csize < self.config.min_cluster_size:
                continue
            if self.config.max_cluster_size is not None and csize > self.config.max_cluster_size:
                continue
            labels[np.asarray(component, dtype=int)] = current_label
            current_label += 1
        return labels

    def _apply_cluster_size_filter(self, labels: np.ndarray) -> np.ndarray:
        """Filter labels by cluster size constraints and remap cluster IDs."""
        filtered = labels.copy()
        unique_labels = [int(v) for v in np.unique(labels) if v >= 0]
        for label in unique_labels:
            size = int((labels == label).sum())
            too_small = size < self.config.min_cluster_size
            too_large = self.config.max_cluster_size is not None and size > self.config.max_cluster_size
            if too_small or too_large:
                filtered[labels == label] = -1

        valid = sorted(int(v) for v in np.unique(filtered) if v >= 0)
        remap = {old: new for new, old in enumerate(valid)}
        for old, new in remap.items():
            filtered[filtered == old] = new
        return filtered

    def compute_cluster_infos(self, cloud: o3d.geometry.PointCloud, labels: np.ndarray) -> list[ClusterInfo]:
        """Compute per-cluster statistics and optional OBB metadata."""
        points = np.asarray(cloud.points)
        infos: list[ClusterInfo] = []
        self._obb_info = {}
        cluster_labels = sorted(int(v) for v in np.unique(labels) if v >= 0)

        for cid in cluster_labels:
            idx = np.where(labels == cid)[0]
            subset = points[idx]
            if len(subset) == 0:
                continue
            min_xyz = subset.min(axis=0)
            max_xyz = subset.max(axis=0)
            extent = max_xyz - min_xyz
            volume = float(extent[0] * extent[1] * extent[2])
            density = None if volume <= 0 else float(len(subset) / volume)
            infos.append(
                ClusterInfo(
                    cluster_id=cid,
                    label=cid,
                    point_count=int(len(subset)),
                    centroid=[float(v) for v in subset.mean(axis=0)],
                    bbox_min=[float(v) for v in min_xyz],
                    bbox_max=[float(v) for v in max_xyz],
                    bbox_extent=[float(v) for v in extent],
                    bbox_volume=volume,
                    density=density,
                    is_noise=False,
                )
            )
            if self.config.compute_oriented_bounding_boxes and len(subset) >= 4:
                sub_cloud = o3d.geometry.PointCloud()
                sub_cloud.points = o3d.utility.Vector3dVector(subset)
                try:
                    obb = sub_cloud.get_oriented_bounding_box()
                    self._obb_info[cid] = {
                        "obb_center_x": float(obb.center[0]),
                        "obb_center_y": float(obb.center[1]),
                        "obb_center_z": float(obb.center[2]),
                        "obb_extent_x": float(obb.extent[0]),
                        "obb_extent_y": float(obb.extent[1]),
                        "obb_extent_z": float(obb.extent[2]),
                        "obb_rotation_matrix": " ".join(f"{v:.6f}" for v in obb.R.flatten()),
                    }
                except Exception:
                    self._obb_info[cid] = {}

        if not self.config.remove_noise:
            noise_idx = np.where(labels == -1)[0]
            if len(noise_idx) > 0:
                subset = points[noise_idx]
                min_xyz = subset.min(axis=0)
                max_xyz = subset.max(axis=0)
                extent = max_xyz - min_xyz
                volume = float(extent[0] * extent[1] * extent[2])
                density = None if volume <= 0 else float(len(subset) / volume)
                infos.append(
                    ClusterInfo(
                        cluster_id=-1,
                        label=-1,
                        point_count=int(len(subset)),
                        centroid=[float(v) for v in subset.mean(axis=0)],
                        bbox_min=[float(v) for v in min_xyz],
                        bbox_max=[float(v) for v in max_xyz],
                        bbox_extent=[float(v) for v in extent],
                        bbox_volume=volume,
                        density=density,
                        is_noise=True,
                    )
                )
        return infos

    def colorize_clusters(self, cloud: o3d.geometry.PointCloud, labels: np.ndarray) -> o3d.geometry.PointCloud:
        """Colorize clusters deterministically."""
        colored = o3d.geometry.PointCloud(cloud)
        n = len(labels)
        colors = np.zeros((n, 3), dtype=float)
        rng = np.random.default_rng(self.config.random_seed)
        valid_labels = sorted(int(v) for v in np.unique(labels) if v >= 0)
        palette = {label: rng.random(3) for label in valid_labels}

        for i, label in enumerate(labels):
            if label == -1:
                colors[i] = np.array([0.5, 0.5, 0.5]) if self.config.color_noise_gray else np.array([0.0, 0.0, 0.0])
            else:
                colors[i] = palette[int(label)]
        colored.colors = o3d.utility.Vector3dVector(colors)
        return colored

    def save_cluster_labels(self, input_path: Path, labels: np.ndarray, output_path: Path) -> None:
        """Save per-point labels CSV."""
        cloud = self.load_point_cloud(input_path)
        points = np.asarray(cloud.points)
        if len(points) != len(labels):
            raise ValueError("Label count does not match point count.")

        rows: dict[str, Any] = {
            "point_index": np.arange(len(points), dtype=int),
            "x": points[:, 0],
            "y": points[:, 1],
            "z": points[:, 2],
            "cluster_label": labels,
            "is_noise": labels == -1,
        }
        if cloud.has_colors():
            colors = np.asarray(cloud.colors)
            rows["r"] = colors[:, 0]
            rows["g"] = colors[:, 1]
            rows["b"] = colors[:, 2]
        df = pd.DataFrame(rows)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)

    def save_cluster_stats(self, cluster_infos: list[ClusterInfo], output_path: Path) -> None:
        """Save per-cluster statistics CSV."""
        rows: list[dict[str, Any]] = []
        for info in cluster_infos:
            row: dict[str, Any] = {
                "cluster_id": info.cluster_id,
                "label": info.label,
                "point_count": info.point_count,
                "centroid_x": info.centroid[0],
                "centroid_y": info.centroid[1],
                "centroid_z": info.centroid[2],
                "bbox_min_x": info.bbox_min[0],
                "bbox_min_y": info.bbox_min[1],
                "bbox_min_z": info.bbox_min[2],
                "bbox_max_x": info.bbox_max[0],
                "bbox_max_y": info.bbox_max[1],
                "bbox_max_z": info.bbox_max[2],
                "extent_x": info.bbox_extent[0],
                "extent_y": info.bbox_extent[1],
                "extent_z": info.bbox_extent[2],
                "bbox_volume": info.bbox_volume,
                "density": info.density,
                "is_noise": info.is_noise,
            }
            if info.cluster_id in self._obb_info and self._obb_info[info.cluster_id]:
                row.update(self._obb_info[info.cluster_id])
            rows.append(row)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(rows).to_csv(output_path, index=False)

    def save_report(self, result: ClusteringResult, input_path: Path, output_path: Path) -> None:
        """Generate Markdown clustering report."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        cluster_sizes = [c.point_count for c in result.cluster_infos if not c.is_noise]
        if cluster_sizes:
            size_line = (
                f"min={min(cluster_sizes)}, max={max(cluster_sizes)}, "
                f"mean={np.mean(cluster_sizes):.2f}, median={np.median(cluster_sizes):.2f}"
            )
        else:
            size_line = "No valid clusters found."

        top_clusters = sorted([c for c in result.cluster_infos if not c.is_noise], key=lambda x: x.point_count, reverse=True)[:10]
        table_lines = ["| Cluster ID | Points | Centroid | BBox Extent | Density |", "|------------|--------|----------|-------------|---------|"]
        for c in top_clusters:
            table_lines.append(
                f"| {c.cluster_id} | {c.point_count} | {c.centroid} | {c.bbox_extent} | "
                f"{'None' if c.density is None else f'{c.density:.6f}'} |"
            )
        if len(top_clusters) == 0:
            table_lines.append("| - | - | - | - | - |")

        report = f"""# Clustering Report

## 1. Input file
`{input_path}`

## 2. Clustering method
`{self.config.method}`

## 3. Configuration
```yaml
{yaml.safe_dump({'clustering': asdict(self.config)}, sort_keys=False)}
```

## 4. Total points
{len(result.labels)}

## 5. Number of valid clusters
{result.valid_clusters}

## 6. Noise points
{result.noise_points}

## 7. Cluster size statistics
{size_line}

## 8. Largest clusters table
{chr(10).join(table_lines)}

## 9. Output files
{chr(10).join(f"- `{k}`: `{v}`" for k, v in result.output_paths.items())}

## 10. Warnings
{chr(10).join(f"- {w}" for w in result.warnings) if result.warnings else "- None"}
"""
        output_path.write_text(report, encoding="utf-8")

    def save_screenshot(self, cloud: o3d.geometry.PointCloud, output_path: Path) -> None:
        """Save a screenshot of clustered cloud using Open3D visualizer."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        vis = o3d.visualization.Visualizer()
        vis.create_window(visible=False)
        vis.add_geometry(cloud)
        vis.poll_events()
        vis.update_renderer()
        vis.capture_screen_image(str(output_path), do_render=True)
        vis.destroy_window()

    def cluster(self, cloud: o3d.geometry.PointCloud) -> ClusteringResult:
        """Run clustering and return in-memory result."""
        t0 = perf_counter()
        warnings: list[str] = []
        if cloud.is_empty():
            raise ValueError("Point cloud is empty.")

        raw_labels = self.run_dbscan(cloud) if self.config.method == "dbscan" else self.run_euclidean_clustering(cloud)
        labels = self._apply_cluster_size_filter(raw_labels)
        noise_points = int((labels == -1).sum())
        cluster_infos = self.compute_cluster_infos(cloud, labels)
        valid_clusters = len([c for c in cluster_infos if not c.is_noise])
        if valid_clusters == 0:
            warnings.append("No valid clusters found after filtering.")
        if noise_points == len(labels):
            warnings.append("All points were classified as noise.")

        colored = self.colorize_clusters(cloud, labels)
        return ClusteringResult(
            labels=labels,
            clustered_cloud=colored,
            cluster_infos=cluster_infos,
            noise_points=noise_points,
            valid_clusters=valid_clusters,
            processing_time_sec=perf_counter() - t0,
            output_paths={},
            warnings=warnings,
        )

    def cluster_file(self, input_path: Path, output_dir: Path) -> ClusteringResult:
        """Cluster cloud from file and save all required outputs."""
        cloud = self.load_point_cloud(input_path)
        result = self.cluster(cloud)

        output_dir.mkdir(parents=True, exist_ok=True)
        report_dir = Path("outputs/reports/clustering")
        report_dir.mkdir(parents=True, exist_ok=True)
        base = input_path.stem
        clustered_path = output_dir / f"{base}_clusters.ply"
        labels_csv = output_dir / f"{base}_cluster_labels.csv"
        stats_csv = output_dir / f"{base}_cluster_stats.csv"
        report_md = report_dir / f"{base}_cluster_report.md"
        screenshot = output_dir / f"{base}_clusters.png"

        ok = o3d.io.write_point_cloud(str(clustered_path), result.clustered_cloud)
        if not ok:
            raise RuntimeError(f"Failed to save clustered point cloud: {clustered_path}")
        self.save_cluster_labels(input_path, result.labels, labels_csv)
        self.save_cluster_stats(result.cluster_infos, stats_csv)

        output_paths: dict[str, str] = {
            "clustered_cloud": str(clustered_path),
            "cluster_labels_csv": str(labels_csv),
            "cluster_stats_csv": str(stats_csv),
            "cluster_report_md": str(report_md),
        }
        if self.config.save_screenshot:
            try:
                self.save_screenshot(result.clustered_cloud, screenshot)
                output_paths["screenshot"] = str(screenshot)
            except Exception as exc:
                result.warnings.append(f"Screenshot export failed: {exc}")

        result.output_paths = output_paths
        self.save_report(result, input_path, report_md)
        return result


def load_clustering_config(config_path: Path | None) -> ClusteringConfig:
    """Load clustering config from YAML."""
    if config_path is None:
        return ClusteringConfig()
    if not config_path.exists():
        raise FileNotFoundError(f"Config file does not exist: {config_path}")
    try:
        raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML in config '{config_path}': {exc}") from exc
    section = raw.get("clustering", raw)
    if not isinstance(section, dict):
        raise ValueError(f"Invalid clustering config format in '{config_path}'.")
    return ClusteringConfig(**section)


def _apply_overrides(config: ClusteringConfig, args: argparse.Namespace) -> ClusteringConfig:
    updated = ClusteringConfig(**asdict(config))
    if args.method is not None:
        updated.method = args.method
    if args.eps is not None:
        updated.eps = args.eps
    if args.min_points is not None:
        updated.min_points = args.min_points
    if args.euclidean_tolerance is not None:
        updated.euclidean_tolerance = args.euclidean_tolerance
    if args.min_cluster_size is not None:
        updated.min_cluster_size = args.min_cluster_size
    if args.max_cluster_size is not None:
        updated.max_cluster_size = args.max_cluster_size
    if args.remove_noise:
        updated.remove_noise = True
    if args.save_screenshot:
        updated.save_screenshot = True
    return updated


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="StreetScanAI clustering subsystem")
    parser.add_argument("--input", required=True, help="Input point cloud path")
    parser.add_argument("--output-dir", default="outputs/clusters", help="Output directory")
    parser.add_argument("--config", default="configs/clustering.yaml", help="Clustering YAML config")
    parser.add_argument("--method", choices=["dbscan", "euclidean"], default=None)
    parser.add_argument("--eps", type=float, default=None)
    parser.add_argument("--min-points", type=int, default=None)
    parser.add_argument("--euclidean-tolerance", type=float, default=None)
    parser.add_argument("--min-cluster-size", type=int, default=None)
    parser.add_argument("--max-cluster-size", type=int, default=None)
    parser.add_argument("--remove-noise", action="store_true")
    parser.add_argument("--save-screenshot", action="store_true")
    return parser


def run_from_args(args: argparse.Namespace) -> ClusteringResult:
    """Run clustering from argparse namespace."""
    cfg = load_clustering_config(Path(args.config) if args.config else None)
    cfg = _apply_overrides(cfg, args)
    clusterer = PointCloudClusterer(cfg)
    return clusterer.cluster_file(Path(args.input), Path(args.output_dir))


def main() -> None:
    """CLI entrypoint for direct clustering script execution."""
    parser = _build_parser()
    args = parser.parse_args()
    try:
        result = run_from_args(args)
    except Exception as exc:
        print(f"[ERROR] Clustering failed: {exc}")
        raise SystemExit(1) from exc
    print(
        "[OK] Clustering completed. "
        f"Valid clusters: {result.valid_clusters}, noise points: {result.noise_points}."
    )


if __name__ == "__main__":
    main()


def run_dbscan(cloud: o3d.geometry.PointCloud, eps: float, min_points: int) -> np.ndarray:
    """Backward-compatible DBSCAN helper used by existing modules."""
    cfg = ClusteringConfig(method="dbscan", eps=eps, min_points=min_points)
    return PointCloudClusterer(cfg).run_dbscan(cloud)
