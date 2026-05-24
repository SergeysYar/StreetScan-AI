"""CLI helper functions."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from src.utils.config_utils import load_yaml


def load_project_config(config_path: str | Path) -> dict[str, Any]:
    """Load full project configuration."""
    return load_yaml(Path(config_path))
