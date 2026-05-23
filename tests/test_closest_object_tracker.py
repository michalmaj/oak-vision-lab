import numpy as np
import pytest

from oak_vision_lab.demos.closest_object_tracker import (
    TrackingRegion,
    compute_region_mean_disparity,
    create_tracking_grid,
    find_best_region,
    find_closest_object_region,
    get_tracker_message,
    normalize_disparity_value,
    scale_region,
    score_tracking_regions,
)
from oak_vision_lab.depth.proximity import ProximityLevel


def test_create_tracking_grid_returns_expected_number_of_regions() -> None:
    regions = create_tracking_grid(
        frame_width=120,
        frame_height=90,
        rows=3,
        columns=4,
    )

    assert len(regions) == 12


def test_create_tracking_grid_covers_frame_with_remainder() -> None:
    regions = create_tracking_grid(
        frame_width=10,
        frame_height=7,
        rows=2,
        columns=3,
    )

    assert regions[0] == TrackingRegion(x=0, y=0, width=3, height=3)
    assert regions[-1] == TrackingRegion(x=6, y=3, width=4, height=4)
    assert regions[-1].x2 == 10
    assert regions[-1].y2 == 7


def test_create_tracking_grid_rejects_invalid_frame_dimensions() -> None:
    with pytest.raises(ValueError, match="frame dimensions must be positive"):
        create_tracking_grid(frame_width=0, frame_height=10)


def test_create_tracking_grid_rejects_invalid_grid_shape() -> None:
    with pytest.raises(ValueError, match="rows and columns must be positive"):
        create_tracking_grid(frame_width=10, frame_height=10, rows=0, columns=3)


def test_compute_region_mean_disparity_ignores_zero_values() -> None:
    frame = np.array(
        [
            [0, 0, 0, 0],
            [0, 10, 20, 0],
            [0, 30, 40, 0],
            [0, 0, 0, 0],
        ],
        dtype=np.uint8,
    )
    region = TrackingRegion(x=1, y=1, width=2, height=2)

    result = compute_region_mean_disparity(frame, region)

    assert result == 25.0


def test_compute_region_mean_disparity_returns_zero_without_valid_pixels() -> None:
    frame = np.zeros((4, 4), dtype=np.uint8)
    region = TrackingRegion(x=1, y=1, width=2, height=2)

    result = compute_region_mean_disparity(frame, region)

    assert result == 0.0


def test_score_tracking_regions_returns_scores_for_each_region() -> None:
    frame = np.array(
        [
            [10, 10, 50, 50],
            [10, 10, 50, 50],
        ],
        dtype=np.uint8,
    )
    regions = [
        TrackingRegion(x=0, y=0, width=2, height=2),
        TrackingRegion(x=2, y=0, width=2, height=2),
    ]

    scores = score_tracking_regions(disparity_frame=frame, regions=regions)

    assert len(scores) == 2
    assert scores[0].mean_disparity == 10.0
    assert scores[1].mean_disparity == 50.0


def test_find_best_region_returns_region_with_highest_score() -> None:
    frame = np.array(
        [
            [10, 10, 50, 50],
            [10, 10, 50, 50],
        ],
        dtype=np.uint8,
    )
    regions = [
        TrackingRegion(x=0, y=0, width=2, height=2),
        TrackingRegion(x=2, y=0, width=2, height=2),
    ]
    scores = score_tracking_regions(disparity_frame=frame, regions=regions)

    best_score = find_best_region(scores)

    assert best_score is not None
    assert best_score.region == regions[1]
    assert best_score.mean_disparity == 50.0


def test_find_best_region_returns_none_for_empty_scores() -> None:
    assert find_best_region([]) is None


def test_find_closest_object_region_detects_highest_disparity_cell() -> None:
    frame = np.zeros((6, 8), dtype=np.uint8)
    frame[2:4, 4:6] = 60

    result = find_closest_object_region(
        disparity_frame=frame,
        rows=3,
        columns=4,
        min_mean_disparity=5.0,
    )

    assert result.detected
    assert result.region == TrackingRegion(x=4, y=2, width=2, height=2)
    assert result.mean_disparity == 60.0


def test_find_closest_object_region_returns_no_detection_below_threshold() -> None:
    frame = np.ones((6, 8), dtype=np.uint8) * 2

    result = find_closest_object_region(
        disparity_frame=frame,
        rows=3,
        columns=4,
        min_mean_disparity=5.0,
    )

    assert not result.detected
    assert result.region is None
    assert result.mean_disparity == 0.0


def test_scale_region_scales_coordinates_between_frame_sizes() -> None:
    region = TrackingRegion(x=10, y=20, width=30, height=40)

    scaled = scale_region(
        region=region,
        source_width=100,
        source_height=200,
        target_width=200,
        target_height=100,
    )

    assert scaled == TrackingRegion(x=20, y=10, width=60, height=20)


def test_scale_region_rejects_invalid_source_dimensions() -> None:
    with pytest.raises(ValueError, match="source dimensions must be positive"):
        scale_region(
            region=TrackingRegion(x=0, y=0, width=10, height=10),
            source_width=0,
            source_height=100,
            target_width=100,
            target_height=100,
        )


def test_scale_region_rejects_invalid_target_dimensions() -> None:
    with pytest.raises(ValueError, match="target dimensions must be positive"):
        scale_region(
            region=TrackingRegion(x=0, y=0, width=10, height=10),
            source_width=100,
            source_height=100,
            target_width=0,
            target_height=100,
        )


def test_normalize_disparity_value_returns_ratio() -> None:
    result = normalize_disparity_value(mean_disparity=25.0, max_disparity=100.0)

    assert result == 0.25


def test_normalize_disparity_value_clamps_to_one() -> None:
    result = normalize_disparity_value(mean_disparity=150.0, max_disparity=100.0)

    assert result == 1.0


def test_normalize_disparity_value_handles_invalid_max_disparity() -> None:
    result = normalize_disparity_value(mean_disparity=25.0, max_disparity=0.0)

    assert result == 0.0


def test_get_tracker_message_returns_no_detection_message() -> None:
    message = get_tracker_message(
        detected=False,
        proximity_level=ProximityLevel.SAFE,
    )

    assert "No close object" in message


def test_get_tracker_message_returns_safe_message() -> None:
    message = get_tracker_message(
        detected=True,
        proximity_level=ProximityLevel.SAFE,
    )

    assert "far away" in message


def test_get_tracker_message_returns_near_message() -> None:
    message = get_tracker_message(
        detected=True,
        proximity_level=ProximityLevel.NEAR,
    )

    assert "near" in message


def test_get_tracker_message_returns_very_close_message() -> None:
    message = get_tracker_message(
        detected=True,
        proximity_level=ProximityLevel.VERY_CLOSE,
    )

    assert "very close" in message
