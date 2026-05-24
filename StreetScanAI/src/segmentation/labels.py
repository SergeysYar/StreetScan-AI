"""Semantic class definitions and label helper functions."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SemanticClass:
    """Definition of one semantic class."""

    id: int
    name: str
    display_name: str
    color_rgb: tuple[float, float, float]
    description: str


_CLASSES: tuple[SemanticClass, ...] = (
    SemanticClass(0, "unlabeled", "Unlabeled", (0.45, 0.45, 0.45), "Points without confident class assignment."),
    SemanticClass(1, "road", "Road", (0.20, 0.20, 0.20), "Road surface and drivable ground."),
    SemanticClass(2, "building", "Building", (0.20, 0.45, 0.95), "Building facades and large fixed structures."),
    SemanticClass(3, "vehicle", "Vehicle", (0.95, 0.25, 0.20), "Cars, buses, trucks and similar road objects."),
    SemanticClass(4, "pedestrian", "Pedestrian", (1.00, 0.78, 0.20), "Human-scale moving persons."),
    SemanticClass(5, "vegetation", "Vegetation", (0.20, 0.75, 0.25), "Trees, bushes and natural green objects."),
    SemanticClass(6, "pole", "Pole", (0.80, 0.80, 0.15), "Thin vertical structures such as lamp poles."),
    SemanticClass(7, "traffic_sign", "Traffic Sign", (1.00, 0.55, 0.05), "Traffic signs and similar elevated small objects."),
)

_BY_ID = {c.id: c for c in _CLASSES}
_BY_NAME = {c.name: c for c in _CLASSES}


def get_label_name(label_id: int) -> str:
    """Return canonical class name for label ID."""
    return _BY_ID.get(label_id, _BY_ID[0]).name


def get_label_id(label_name: str) -> int:
    """Return class ID for canonical class name."""
    normalized = label_name.strip().lower()
    if normalized not in _BY_NAME:
        raise ValueError(f"Unknown label name: {label_name}")
    return _BY_NAME[normalized].id


def get_label_color(label_id: int) -> tuple[float, float, float]:
    """Return Open3D-compatible RGB color for label ID."""
    return _BY_ID.get(label_id, _BY_ID[0]).color_rgb


def list_classes() -> list[SemanticClass]:
    """List all configured semantic classes."""
    return list(_CLASSES)


def validate_label_id(label_id: int) -> bool:
    """Check whether label ID exists in configured classes."""
    return label_id in _BY_ID

