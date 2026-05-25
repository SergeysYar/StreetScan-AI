"""Animation export utilities for point cloud turntable rendering."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import open3d as o3d


def export_camera_path_frames(cloud_path: Path, output_dir: Path, config) -> list[Path]:
    """Export camera turntable frames around point cloud."""
    output_dir.mkdir(parents=True, exist_ok=True)
    cloud = o3d.io.read_point_cloud(str(cloud_path))
    if cloud.is_empty():
        raise ValueError(f"Point cloud is empty: {cloud_path}")

    vis = o3d.visualization.Visualizer()
    vis.create_window(visible=False, width=int(config.image_width), height=int(config.image_height))
    vis.add_geometry(cloud)
    opt = vis.get_render_option()
    opt.point_size = float(config.point_size)
    opt.background_color = np.array(config.background_color, dtype=float)
    vc = vis.get_view_control()

    bbox = cloud.get_axis_aligned_bounding_box()
    center = bbox.get_center()
    vc.set_lookat(center)
    vc.set_up(np.array([0.0, 0.0, 1.0]))
    vc.set_zoom(0.8)

    frames: list[Path] = []
    total = max(1, int(config.animation_frames))
    for i in range(total):
        angle = 2.0 * np.pi * (i / total)
        front = np.array([np.cos(angle), np.sin(angle), -0.45])
        vc.set_front(front / np.linalg.norm(front))
        vis.poll_events()
        vis.update_renderer()
        frame_path = output_dir / f"frame_{i:04d}.png"
        vis.capture_screen_image(str(frame_path), do_render=True)
        frames.append(frame_path)

    vis.destroy_window()
    return frames


def export_turntable_gif(cloud_path: Path, output_path: Path, config) -> None:
    """Export turntable GIF if imageio is available; otherwise raise informative error."""
    frames_dir = output_path.parent / f"{output_path.stem}_frames"
    frames = export_camera_path_frames(cloud_path, frames_dir, config)
    try:
        import imageio.v2 as imageio
    except Exception as exc:
        raise RuntimeError(f"imageio unavailable, frames saved to {frames_dir}: {exc}") from exc

    imgs = [imageio.imread(str(p)) for p in frames]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    imageio.mimsave(str(output_path), imgs, fps=max(1, int(config.animation_fps)))
