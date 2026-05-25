"""I/O helpers."""
from __future__ import annotations

from pathlib import Path


def ensure_parent(path: Path) -> None:
    """Ensure parent directory exists."""
    path.parent.mkdir(parents=True, exist_ok=True)
