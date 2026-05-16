import numpy as np
import pytest

from oak_vision_lab.demos.depth_hot_zone_game import (
    HotZoneGameConfig,
    ProximityLevel,
    classify_proximity,
    compute_mean_disparity,
    create_initial_game_state,
    extract_center_roi,
    get_time_left,
    is_game_finished,
    normalize_disparity_frame,
    should_award_points,
    update_game_state,
)


def test_normalize_disparity_frame_returns_uint8_frame() -> None:
    disparity_frame = np.array([[0, 48, 96]], dtype=np.uint8)

    normalized_frame = normalize_disparity_frame(disparity_frame, max_disparity=96.0)

    assert normalized_frame.dtype == np.uint8
    assert normalized_frame.tolist() == [[0, 127, 255]]


def test_extract_center_roi_returns_expected_shape() -> None:
    frame = np.zeros((100, 200), dtype=np.uint8)

    roi = extract_center_roi(frame, roi_scale=0.5)

    assert roi.shape == (50, 100)


def test_compute_mean_disparity_ignores_zero_values() -> None:
    frame = np.array([[0, 10, 20], [0, 0, 30]], dtype=np.uint8)

    mean_disparity = compute_mean_disparity(frame)

    assert mean_disparity == 20.0


@pytest.mark.parametrize(
    ("mean_disparity", "expected_level"),
    [
        (10.0, ProximityLevel.SAFE),
        (25.0, ProximityLevel.NEAR),
        (44.9, ProximityLevel.NEAR),
        (45.0, ProximityLevel.VERY_CLOSE),
    ],
)
def test_classify_proximity_returns_expected_level(
    mean_disparity: float,
    expected_level: ProximityLevel,
) -> None:
    level = classify_proximity(
        mean_disparity,
        near_threshold=25.0,
        very_close_threshold=45.0,
    )

    assert level is expected_level


def test_create_initial_game_state_sets_initial_values() -> None:
    state = create_initial_game_state(current_time=100.0)

    assert state.score == 0
    assert state.start_time == 100.0
    assert state.last_hit_time == float("-inf")


def test_get_time_left_returns_remaining_time() -> None:
    config = HotZoneGameConfig(duration_seconds=30.0)
    state = create_initial_game_state(current_time=100.0)

    time_left = get_time_left(state, config, current_time=112.5)

    assert time_left == 17.5


def test_get_time_left_does_not_return_negative_values() -> None:
    config = HotZoneGameConfig(duration_seconds=30.0)
    state = create_initial_game_state(current_time=100.0)

    time_left = get_time_left(state, config, current_time=200.0)

    assert time_left == 0.0


def test_is_game_finished_returns_true_after_duration() -> None:
    config = HotZoneGameConfig(duration_seconds=30.0)
    state = create_initial_game_state(current_time=100.0)

    assert is_game_finished(state, config, current_time=130.0)


def test_should_award_points_for_near_level() -> None:
    config = HotZoneGameConfig(hit_cooldown_seconds=0.35)
    state = create_initial_game_state(current_time=100.0)

    result = should_award_points(
        ProximityLevel.NEAR,
        state,
        config,
        current_time=100.1,
    )

    assert result


def test_should_not_award_points_for_safe_level() -> None:
    config = HotZoneGameConfig()
    state = create_initial_game_state(current_time=100.0)

    result = should_award_points(
        ProximityLevel.SAFE,
        state,
        config,
        current_time=100.1,
    )

    assert not result


def test_should_not_award_points_during_cooldown() -> None:
    config = HotZoneGameConfig(hit_cooldown_seconds=0.35)
    state = create_initial_game_state(current_time=100.0)
    state, _ = update_game_state(
        ProximityLevel.NEAR,
        state,
        config,
        current_time=100.1,
    )

    result = should_award_points(
        ProximityLevel.NEAR,
        state,
        config,
        current_time=100.2,
    )

    assert not result


def test_update_game_state_awards_points() -> None:
    config = HotZoneGameConfig(points_per_hit=10)
    state = create_initial_game_state(current_time=100.0)

    updated_state, points_awarded = update_game_state(
        ProximityLevel.VERY_CLOSE,
        state,
        config,
        current_time=100.1,
    )

    assert points_awarded
    assert updated_state.score == 10
    assert updated_state.last_hit_time == 100.1


def test_update_game_state_does_not_award_points_after_game_finished() -> None:
    config = HotZoneGameConfig(duration_seconds=30.0)
    state = create_initial_game_state(current_time=100.0)

    updated_state, points_awarded = update_game_state(
        ProximityLevel.VERY_CLOSE,
        state,
        config,
        current_time=131.0,
    )

    assert not points_awarded
    assert updated_state == state
