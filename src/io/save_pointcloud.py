"""Point cloud saving."""
from __future__ import annotations

from pathlib import Path

import open3d as o3d

from src.io.formats import validate_format
from src.utils.io_utils import ensure_parent


def save_point_cloud(cloud: o3d.geometry.PointCloud, path: Path) -> None:
    """Save point cloud to disk."""
    validate_format(path)
    if path.suffix.lower() == ".las":
        raise NotImplementedError("LAS writer placeholder. Integrate laspy in future.")
    ensure_parent(path)
    o3d.io.write_point_cloud(str(path), cloud)
