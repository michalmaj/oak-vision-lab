import numpy as np
import pytest

from oak_vision_lab.demos.object_distance_meter import (
    DistanceMeterStats,
    MeterRegion,
    compute_region_mean_disparity,
    create_meter_segments,
    get_center_meter_region,
    get_proximity_level_rank,
    get_proximity_message,
    normalize_disparity_value,
    update_distance_stats,
)
from oak_vision_lab.depth.proximity import ProximityLevel


def test_get_center_meter_region_returns_centered_region() -> None:
    region = get_center_meter_region(frame_width=100, frame_height=80)

    assert region.width == 34
    assert region.height == 27
    assert region.x == 33
    assert region.y == 26
    assert region.x2 == 67
    assert region.y2 == 53


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
    region = MeterRegion(x=1, y=1, width=2, height=2)

    result = compute_region_mean_disparity(frame, region)

    assert result == 25.0


def test_compute_region_mean_disparity_returns_zero_for_empty_valid_pixels() -> None:
    frame = np.zeros((4, 4), dtype=np.uint8)
    region = MeterRegion(x=1, y=1, width=2, height=2)

    result = compute_region_mean_disparity(frame, region)

    assert result == 0.0


def test_normalize_disparity_value_returns_ratio() -> None:
    result = normalize_disparity_value(mean_disparity=25.0, max_disparity=100.0)

    assert result == 0.25


def test_normalize_disparity_value_clamps_to_zero() -> None:
    result = normalize_disparity_value(mean_disparity=-10.0, max_disparity=100.0)

    assert result == 0.0


def test_normalize_disparity_value_clamps_to_one() -> None:
    result = normalize_disparity_value(mean_disparity=120.0, max_disparity=100.0)

    assert result == 1.0


def test_normalize_disparity_value_handles_invalid_max_disparity() -> None:
    result = normalize_disparity_value(mean_disparity=20.0, max_disparity=0.0)

    assert result == 0.0


def test_create_meter_segments_returns_filled_and_empty_counts() -> None:
    segments = create_meter_segments(normalized_value=0.5, segment_count=20)

    assert segments.filled == 10
    assert segments.empty == 10
    assert segments.total == 20


def test_create_meter_segments_clamps_input_value() -> None:
    segments = create_meter_segments(normalized_value=2.0, segment_count=20)

    assert segments.filled == 20
    assert segments.empty == 0


def test_create_meter_segments_rejects_non_positive_segment_count() -> None:
    with pytest.raises(ValueError, match="segment_count must be positive"):
        create_meter_segments(normalized_value=0.5, segment_count=0)


def test_get_proximity_message_returns_message_for_safe_level() -> None:
    message = get_proximity_message(ProximityLevel.SAFE)

    assert "respectful distance" in message


def test_get_proximity_message_returns_message_for_near_level() -> None:
    message = get_proximity_message(ProximityLevel.NEAR)

    assert "measurement zone" in message


def test_get_proximity_message_returns_message_for_very_close_level() -> None:
    message = get_proximity_message(ProximityLevel.VERY_CLOSE)

    assert "very close" in message


def test_get_proximity_level_rank_orders_levels() -> None:
    assert get_proximity_level_rank(ProximityLevel.SAFE) < get_proximity_level_rank(
        ProximityLevel.NEAR,
    )
    assert get_proximity_level_rank(ProximityLevel.NEAR) < get_proximity_level_rank(
        ProximityLevel.VERY_CLOSE,
    )


def test_update_distance_stats_initializes_empty_stats() -> None:
    stats = update_distance_stats(
        stats=DistanceMeterStats(),
        mean_disparity=30.0,
        proximity_level=ProximityLevel.NEAR,
    )

    assert stats.sample_count == 1
    assert stats.min_disparity == 30.0
    assert stats.max_disparity == 30.0
    assert stats.peak_level == ProximityLevel.NEAR


def test_update_distance_stats_updates_min_max_and_peak_level() -> None:
    stats = DistanceMeterStats(
        sample_count=1,
        min_disparity=30.0,
        max_disparity=30.0,
        peak_level=ProximityLevel.NEAR,
    )

    updated = update_distance_stats(
        stats=stats,
        mean_disparity=50.0,
        proximity_level=ProximityLevel.VERY_CLOSE,
    )

    assert updated.sample_count == 2
    assert updated.min_disparity == 30.0
    assert updated.max_disparity == 50.0
    assert updated.peak_level == ProximityLevel.VERY_CLOSE
