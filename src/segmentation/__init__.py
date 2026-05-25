"""Semantic segmentation package for StreetScanAI."""

from src.segmentation.labels import (
    SemanticClass,
    get_label_color,
    get_label_id,
    get_label_name,
    list_classes,
    validate_label_id,
)
from src.segmentation.semantic_segmentation import (
    SegmentationConfig,
    SegmentationResult,
    SemanticPrediction,
    SemanticSegmenter,
    load_segmentation_config,
)

__all__ = [
    "SemanticClass",
    "SegmentationConfig",
    "SegmentationResult",
    "SemanticPrediction",
    "SemanticSegmenter",
    "get_label_color",
    "get_label_id",
    "get_label_name",
    "list_classes",
    "validate_label_id",
    "load_segmentation_config",
]

