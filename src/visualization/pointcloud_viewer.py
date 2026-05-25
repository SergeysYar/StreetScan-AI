"""General point cloud rendering and screenshot utilities."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import open3d as o3d


@dataclass
class ViewerConfig:
    """Viewer configuration for point cloud rendering."""

    backend: str = "open3d"
    image_width: int = 1600
    image_height: int = 1000
    point_size: float = 2.0
    background_color: tuple[float, float, float] = (1.0, 1.0, 1.0)
    camera_view: str = "isometric"
    show_axes: bool = True
    save_screenshot: bool = True
    interactive: bool = False


def load_cloud(path: Path) -> o3d.geometry.PointCloud:
    """Load point cloud from supported format."""
    if not path.exists():
        raise FileNotFoundError(f"Point cloud not found: {path}")
    if path.suffix.lower() not in {".ply", ".pcd", ".xyz"}:
        raise ValueError(f"Unsupported point cloud extension: {path.suffix}")
    cloud = o3d.io.read_point_cloud(str(path))
    if cloud.is_empty() or len(np.asarray(cloud.points)) == 0:
        raise ValueError(f"Point cloud is empty: {path}")
    return cloud


def create_coordinate_axes(size: float = 1.0) -> o3d.geometry.TriangleMesh:
    """Create coordinate frame mesh."""
    return o3d.geometry.TriangleMesh.create_coordinate_frame(size=size)


def _set_camera(view_control: o3d.visualization.ViewControl, cloud: o3d.geometry.PointCloud, camera_view: str) -> None:
    """Configure camera orientation."""
    bounds = cloud.get_axis_aligned_bounding_box()
    center = bounds.get_center()
    extent = max(bounds.get_extent()) if len(bounds.get_extent()) > 0 else 1.0

    if camera_view == "top":
        front = np.array([0.0, 0.0, -1.0])
        up = np.array([0.0, 1.0, 0.0])
    elif camera_view == "front":
        front = np.array([0.0, -1.0, 0.0])
        up = np.array([0.0, 0.0, 1.0])
    elif camera_view == "side":
        front = np.array([1.0, 0.0, 0.0])
        up = np.array([0.0, 0.0, 1.0])
    else:
        front = np.array([0.8, -0.8, -0.6])
        up = np.array([0.0, 0.0, 1.0])

    view_control.set_lookat(center)
    view_control.set_front(front)
    view_control.set_up(up)
    view_control.set_zoom(0.8 if extent > 0 else 0.7)


def render_pointcloud(cloud: o3d.geometry.PointCloud, output_path: Path, config: ViewerConfig) -> None:
    """Render point cloud screenshot using Open3D backend."""
    if config.backend not in {"open3d", "pyvista"}:
        raise ValueError("backend must be 'open3d' or 'pyvista'")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if config.backend == "pyvista":
        try:
            import pyvista as pv
        except Exception as exc:
            raise RuntimeError(f"PyVista backend unavailable: {exc}") from exc

        pts = np.asarray(cloud.points)
        pdata = pv.PolyData(pts)
        pl = pv.Plotter(off_screen=True, window_size=(config.image_width, config.image_height))
        pl.set_background(config.background_color)
        pl.add_points(pdata, render_points_as_spheres=True, point_size=config.point_size)
        if config.show_axes:
            pl.add_axes()
        pl.show(screenshot=str(output_path), auto_close=True)
        return

    vis = o3d.visualization.Visualizer()
    vis.create_window(visible=False, width=config.image_width, height=config.image_height)
    vis.add_geometry(cloud)
    if config.show_axes:
        vis.add_geometry(create_coordinate_axes(size=1.0))
    opt = vis.get_render_option()
    opt.point_size = float(config.point_size)
    opt.background_color = np.array(config.background_color, dtype=float)
    _set_camera(vis.get_view_control(), cloud, config.camera_view)
    vis.poll_events()
    vis.update_renderer()
    vis.capture_screen_image(str(output_path), do_render=True)
    vis.destroy_window()


def open_interactive_viewer(cloud: o3d.geometry.PointCloud, config: ViewerConfig) -> None:
    """Open interactive point cloud window."""
    if config.backend == "pyvista":
        try:
            import pyvista as pv
        except Exception as exc:
            raise RuntimeError(f"PyVista backend unavailable: {exc}") from exc
        pl = pv.Plotter(window_size=(config.image_width, config.image_height))
        pl.add_points(np.asarray(cloud.points), render_points_as_spheres=True, point_size=config.point_size)
        if config.show_axes:
            pl.add_axes()
        pl.show()
        return
    o3d.visualization.draw_geometries([cloud, create_coordinate_axes(1.0)] if config.show_axes else [cloud])
