"""Benchmark metric computation."""
from __future__ import annotations


def compute_fps(runtime_sec: float) -> float:
    """Compute frames per second from runtime."""
    return 0.0 if runtime_sec <= 0 else 1.0 / runtime_sec
