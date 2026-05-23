"""Closest object tracker logic based on stereo disparity."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from oak_vision_lab.depth.proximity import ProximityLevel

DEFAULT_GRID_ROWS = 3
DEFAULT_GRID_COLUMNS = 4
DEFAULT_MIN_MEAN_DISPARITY = 5.0

DEFAULT_NEAR_THRESHOLD = 25.0
DEFAULT_VERY_CLOSE_THRESHOLD = 45.0


@dataclass(frozen=True)
class TrackingRegion:
    """Rectangular tracking region in image coordinates."""

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
class RegionScore:
    """Mean disparity score for a tracking region."""

    region: TrackingRegion
    mean_disparity: float


@dataclass(frozen=True)
class ClosestObjectResult:
    """Closest object tracking result."""

    region: TrackingRegion | None
    mean_disparity: float
    detected: bool


def create_tracking_grid(
    *,
    frame_width: int,
    frame_height: int,
    rows: int = DEFAULT_GRID_ROWS,
    columns: int = DEFAULT_GRID_COLUMNS,
) -> list[TrackingRegion]:
    """Create a regular grid of tracking regions."""

    if frame_width <= 0 or frame_height <= 0:
        msg = "frame dimensions must be positive"
        raise ValueError(msg)

    if rows <= 0 or columns <= 0:
        msg = "rows and columns must be positive"
        raise ValueError(msg)

    cell_width = frame_width // columns
    cell_height = frame_height // rows

    regions: list[TrackingRegion] = []

    for row in range(rows):
        for column in range(columns):
            x = column * cell_width
            y = row * cell_height

            width = frame_width - x if column == columns - 1 else cell_width

            height = frame_height - y if row == rows - 1 else cell_height

            regions.append(
                TrackingRegion(
                    x=x,
                    y=y,
                    width=width,
                    height=height,
                ),
            )

    return regions


def compute_region_mean_disparity(
    disparity_frame: np.ndarray,
    region: TrackingRegion,
) -> float:
    """Compute mean non-zero disparity inside a tracking region."""

    roi = disparity_frame[region.y : region.y2, region.x : region.x2]

    if roi.size == 0:
        return 0.0

    valid_pixels = roi[roi > 0]

    if valid_pixels.size == 0:
        return 0.0

    return float(np.mean(valid_pixels))


def score_tracking_regions(
    *,
    disparity_frame: np.ndarray,
    regions: list[TrackingRegion],
) -> list[RegionScore]:
    """Compute mean disparity scores for tracking regions."""

    return [
        RegionScore(
            region=region,
            mean_disparity=compute_region_mean_disparity(
                disparity_frame,
                region,
            ),
        )
        for region in regions
    ]


def find_best_region(
    scores: list[RegionScore],
) -> RegionScore | None:
    """Return the region with the highest mean disparity."""

    if not scores:
        return None

    return max(scores, key=lambda score: score.mean_disparity)


def find_closest_object_region(
    *,
    disparity_frame: np.ndarray,
    rows: int = DEFAULT_GRID_ROWS,
    columns: int = DEFAULT_GRID_COLUMNS,
    min_mean_disparity: float = DEFAULT_MIN_MEAN_DISPARITY,
) -> ClosestObjectResult:
    """Find the grid region most likely to contain the closest object."""

    frame_height, frame_width = disparity_frame.shape[:2]

    regions = create_tracking_grid(
        frame_width=frame_width,
        frame_height=frame_height,
        rows=rows,
        columns=columns,
    )
    scores = score_tracking_regions(
        disparity_frame=disparity_frame,
        regions=regions,
    )
    best_score = find_best_region(scores)

    if best_score is None or best_score.mean_disparity < min_mean_disparity:
        return ClosestObjectResult(
            region=None,
            mean_disparity=0.0,
            detected=False,
        )

    return ClosestObjectResult(
        region=best_score.region,
        mean_disparity=best_score.mean_disparity,
        detected=True,
    )


def scale_region(
    *,
    region: TrackingRegion,
    source_width: int,
    source_height: int,
    target_width: int,
    target_height: int,
) -> TrackingRegion:
    """Scale a region from one frame size to another."""

    if source_width <= 0 or source_height <= 0:
        msg = "source dimensions must be positive"
        raise ValueError(msg)

    if target_width <= 0 or target_height <= 0:
        msg = "target dimensions must be positive"
        raise ValueError(msg)

    scale_x = target_width / source_width
    scale_y = target_height / source_height

    return TrackingRegion(
        x=round(region.x * scale_x),
        y=round(region.y * scale_y),
        width=round(region.width * scale_x),
        height=round(region.height * scale_y),
    )


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


def get_tracker_message(
    *,
    detected: bool,
    proximity_level: ProximityLevel,
) -> str:
    """Return a short HUD message for the tracker state."""

    if not detected:
        return "No close object detected."

    messages = {
        ProximityLevel.SAFE: "Closest object detected, but still far away.",
        ProximityLevel.NEAR: "Closest object is near the camera.",
        ProximityLevel.VERY_CLOSE: "Closest object is very close.",
    }

    return messages[proximity_level]
