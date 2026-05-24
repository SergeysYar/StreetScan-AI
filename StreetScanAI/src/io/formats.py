"""Supported point cloud formats."""
from __future__ import annotations

from pathlib import Path

SUPPORTED_FORMATS = {".ply", ".pcd", ".xyz", ".las"}


def validate_format(path: Path) -> None:
    """Validate point cloud file extension."""
    if path.suffix.lower() not in SUPPORTED_FORMATS:
        raise ValueError(f"Unsupported format: {path.suffix}")
