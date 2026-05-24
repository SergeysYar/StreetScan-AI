"""Point cloud visualization using Open3D."""
from __future__ import annotations

from pathlib import Path

import open3d as o3d


def save_screenshot(cloud: o3d.geometry.PointCloud, path: Path) -> None:
    """Off-screen style screenshot helper for future expansion."""
    path.parent.mkdir(parents=True, exist_ok=True)
    o3d.io.write_point_cloud(str(path.with_suffix(".ply")), cloud)
