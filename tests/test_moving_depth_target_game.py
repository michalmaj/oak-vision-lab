import random

import numpy as np
import pytest

from oak_vision_lab.demos.moving_depth_target_game import (
    MovingTargetGameConfig,
    ProximityLevel,
    TargetZone,
    classify_proximity,
    compute_mean_disparity,
    create_initial_game_state,
    extract_target_roi,
    generate_random_target,
    get_target_bounds,
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


def test_generate_random_target_uses_expected_range() -> None:
    rng = random.Random(123)

    target = generate_random_target(
        rng,
        scale=0.25,
        min_center=0.2,
        max_center=0.8,
    )

    assert 0.2 <= target.center_x <= 0.8
    assert 0.2 <= target.center_y <= 0.8
    assert target.scale == 0.25


def test_get_target_bounds_returns_expected_bounds() -> None:
    target = TargetZone(center_x=0.5, center_y=0.5, scale=0.25)

    bounds = get_target_bounds((100, 200), target)

    assert bounds == (75, 38, 125, 63)


def test_extract_target_roi_returns_expected_shape() -> None:
    frame = np.zeros((100, 200), dtype=np.uint8)
    target = TargetZone(center_x=0.5, center_y=0.5, scale=0.5)

    roi = extract_target_roi(frame, target)

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
    target = TargetZone(center_x=0.5, center_y=0.5)

    state = create_initial_game_state(current_time=100.0, target=target)

    assert state.score == 0
    assert state.start_time == 100.0
    assert state.last_hit_time == float("-inf")
    assert state.target == target


def test_get_time_left_returns_remaining_time() -> None:
    config = MovingTargetGameConfig(duration_seconds=30.0)
    target = TargetZone(center_x=0.5, center_y=0.5)
    state = create_initial_game_state(current_time=100.0, target=target)

    time_left = get_time_left(state, config, current_time=112.5)

    assert time_left == 17.5


def test_is_game_finished_returns_true_after_duration() -> None:
    config = MovingTargetGameConfig(duration_seconds=30.0)
    target = TargetZone(center_x=0.5, center_y=0.5)
    state = create_initial_game_state(current_time=100.0, target=target)

    assert is_game_finished(state, config, current_time=130.0)


def test_should_award_points_for_near_level() -> None:
    config = MovingTargetGameConfig(hit_cooldown_seconds=0.35)
    target = TargetZone(center_x=0.5, center_y=0.5)
    state = create_initial_game_state(current_time=100.0, target=target)

    result = should_award_points(
        ProximityLevel.NEAR,
        state,
        config,
        current_time=100.1,
    )

    assert result


def test_should_not_award_points_for_safe_level() -> None:
    config = MovingTargetGameConfig()
    target = TargetZone(center_x=0.5, center_y=0.5)
    state = create_initial_game_state(current_time=100.0, target=target)

    result = should_award_points(
        ProximityLevel.SAFE,
        state,
        config,
        current_time=100.1,
    )

    assert not result


def test_should_not_award_points_during_cooldown() -> None:
    config = MovingTargetGameConfig(hit_cooldown_seconds=0.35)
    target = TargetZone(center_x=0.5, center_y=0.5)
    next_target = TargetZone(center_x=0.7, center_y=0.7)
    state = create_initial_game_state(current_time=100.0, target=target)

    state, _ = update_game_state(
        ProximityLevel.NEAR,
        state,
        config,
        current_time=100.1,
        next_target=next_target,
    )

    result = should_award_points(
        ProximityLevel.NEAR,
        state,
        config,
        current_time=100.2,
    )

    assert not result


def test_update_game_state_awards_points_and_moves_target() -> None:
    config = MovingTargetGameConfig(points_per_hit=10)
    target = TargetZone(center_x=0.5, center_y=0.5)
    next_target = TargetZone(center_x=0.7, center_y=0.3)
    state = create_initial_game_state(current_time=100.0, target=target)

    updated_state, points_awarded = update_game_state(
        ProximityLevel.VERY_CLOSE,
        state,
        config,
        current_time=100.1,
        next_target=next_target,
    )

    assert points_awarded
    assert updated_state.score == 10
    assert updated_state.last_hit_time == 100.1
    assert updated_state.target == next_target


def test_update_game_state_does_not_award_points_after_game_finished() -> None:
    config = MovingTargetGameConfig(duration_seconds=30.0)
    target = TargetZone(center_x=0.5, center_y=0.5)
    next_target = TargetZone(center_x=0.7, center_y=0.3)
    state = create_initial_game_state(current_time=100.0, target=target)

    updated_state, points_awarded = update_game_state(
        ProximityLevel.VERY_CLOSE,
        state,
        config,
        current_time=131.0,
        next_target=next_target,
    )

    assert not points_awarded
    assert updated_state == state
