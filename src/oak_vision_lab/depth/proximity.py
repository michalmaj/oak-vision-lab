"""Reusable proximity classification helpers."""

from __future__ import annotations

from enum import Enum


class ProximityLevel(Enum):
    """Detected proximity level based on disparity statistics."""

    SAFE = "SAFE"
    NEAR = "NEAR"
    VERY_CLOSE = "VERY CLOSE"


def classify_proximity(
    mean_disparity: float,
    near_threshold: float,
    very_close_threshold: float,
) -> ProximityLevel:
    """Classify proximity based on mean disparity."""

    if near_threshold < 0.0 or very_close_threshold < 0.0:
        msg = "thresholds must be non-negative"
        raise ValueError(msg)

    if very_close_threshold <= near_threshold:
        msg = "very_close_threshold must be greater than near_threshold"
        raise ValueError(msg)

    if mean_disparity >= very_close_threshold:
        return ProximityLevel.VERY_CLOSE

    if mean_disparity >= near_threshold:
        return ProximityLevel.NEAR

    return ProximityLevel.SAFE


def get_alert_color(level: ProximityLevel) -> tuple[int, int, int]:
    """Return an OpenCV BGR color for a proximity level."""

    if level is ProximityLevel.VERY_CLOSE:
        return (0, 0, 255)

    if level is ProximityLevel.NEAR:
        return (0, 165, 255)

    return (0, 255, 0)
