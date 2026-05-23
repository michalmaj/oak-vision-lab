"""Object distance meter logic based on stereo disparity."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from oak_vision_lab.depth.proximity import ProximityLevel

DEFAULT_NEAR_THRESHOLD = 25.0
DEFAULT_VERY_CLOSE_THRESHOLD = 45.0

METER_REGION_WIDTH_RATIO = 0.34
METER_REGION_HEIGHT_RATIO = 0.34

DEFAULT_METER_SEGMENTS = 20


@dataclass(frozen=True)
class MeterRegion:
    """Rectangular measurement region in image coordinates."""

    x: int
    y: int
    width: int
    height: int

    @property
    def x2(self) -> int:
        """Return the right edge coordinate."""

        return self.x + self.width

    @property
    def y2(self) -> int:
        """Return the bottom edge coordinate."""

        return self.y + self.height


@dataclass(frozen=True)
class MeterSegments:
    """Text-friendly representation of a proximity meter."""

    filled: int
    empty: int

    @property
    def total(self) -> int:
        """Return the total number of meter segments."""

        return self.filled + self.empty


@dataclass(frozen=True)
class DistanceMeterStats:
    """Aggregated distance meter statistics."""

    sample_count: int = 0
    min_disparity: float | None = None
    max_disparity: float | None = None
    peak_level: ProximityLevel = ProximityLevel.SAFE


def get_center_meter_region(
    *,
    frame_width: int,
    frame_height: int,
    width_ratio: float = METER_REGION_WIDTH_RATIO,
    height_ratio: float = METER_REGION_HEIGHT_RATIO,
) -> MeterRegion:
    """Return a centered measurement region for the given frame size."""

    width = int(frame_width * width_ratio)
    height = int(frame_height * height_ratio)
    x = (frame_width - width) // 2
    y = (frame_height - height) // 2

    return MeterRegion(x=x, y=y, width=width, height=height)


def compute_region_mean_disparity(
    disparity_frame: np.ndarray,
    region: MeterRegion,
) -> float:
    """Compute mean non-zero disparity inside the measurement region."""

    roi = disparity_frame[region.y : region.y2, region.x : region.x2]

    if roi.size == 0:
        return 0.0

    valid_pixels = roi[roi > 0]

    if valid_pixels.size == 0:
        return 0.0

    return float(np.mean(valid_pixels))


def normalize_disparity_value(
    *,
    mean_disparity: float,
    max_disparity: float,
) -> float:
    """Normalize disparity to a 0.0-1.0 range."""

    if max_disparity <= 0.0:
        return 0.0

    normalized = mean_disparity / max_disparity

    return max(0.0, min(1.0, normalized))


def create_meter_segments(
    *,
    normalized_value: float,
    segment_count: int = DEFAULT_METER_SEGMENTS,
) -> MeterSegments:
    """Create filled and empty segment counts for a proximity meter."""

    if segment_count <= 0:
        msg = "segment_count must be positive"
        raise ValueError(msg)

    clamped_value = max(0.0, min(1.0, normalized_value))
    filled = round(clamped_value * segment_count)
    empty = segment_count - filled

    return MeterSegments(filled=filled, empty=empty)


def get_proximity_message(proximity_level: ProximityLevel) -> str:
    """Return a short HUD message for the current proximity level."""

    messages = {
        ProximityLevel.SAFE: "Object is keeping a respectful distance.",
        ProximityLevel.NEAR: "Object entered the measurement zone.",
        ProximityLevel.VERY_CLOSE: "Object is very close to the camera.",
    }

    return messages[proximity_level]


def get_proximity_level_rank(proximity_level: ProximityLevel) -> int:
    """Return numeric rank for comparing proximity levels."""

    ranks = {
        ProximityLevel.SAFE: 0,
        ProximityLevel.NEAR: 1,
        ProximityLevel.VERY_CLOSE: 2,
    }

    return ranks[proximity_level]


def update_distance_stats(
    *,
    stats: DistanceMeterStats,
    mean_disparity: float,
    proximity_level: ProximityLevel,
) -> DistanceMeterStats:
    """Return updated distance meter statistics."""

    if stats.min_disparity is None:
        min_disparity = mean_disparity
    else:
        min_disparity = min(stats.min_disparity, mean_disparity)

    if stats.max_disparity is None:
        max_disparity = mean_disparity
    else:
        max_disparity = max(stats.max_disparity, mean_disparity)

    if get_proximity_level_rank(proximity_level) > get_proximity_level_rank(
        stats.peak_level,
    ):
        peak_level = proximity_level
    else:
        peak_level = stats.peak_level

    return DistanceMeterStats(
        sample_count=stats.sample_count + 1,
        min_disparity=min_disparity,
        max_disparity=max_disparity,
        peak_level=peak_level,
    )
