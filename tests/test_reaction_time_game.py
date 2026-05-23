import random

import numpy as np

from oak_vision_lab.demos.reaction_time_game import (
    ReactionPhase,
    TargetRegion,
    activate_target,
    compute_average_reaction_time,
    compute_best_reaction_time,
    compute_reaction_time,
    compute_region_mean_disparity,
    create_initial_state,
    finish_game,
    format_time_value,
    get_center_target_region,
    is_successful_hit,
    register_hit,
    should_activate_target,
    update_game_state,
)
from oak_vision_lab.depth.proximity import ProximityLevel


def test_get_center_target_region_returns_centered_region() -> None:
    region = get_center_target_region(frame_width=100, frame_height=80)

    assert region.width == 34
    assert region.height == 27
    assert region.x == 33
    assert region.y == 26


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
    region = TargetRegion(x=1, y=1, width=2, height=2)

    result = compute_region_mean_disparity(frame, region)

    assert result == 25.0


def test_compute_region_mean_disparity_returns_zero_for_empty_valid_pixels() -> None:
    frame = np.zeros((4, 4), dtype=np.uint8)
    region = TargetRegion(x=1, y=1, width=2, height=2)

    result = compute_region_mean_disparity(frame, region)

    assert result == 0.0


def test_compute_reaction_time_returns_elapsed_time() -> None:
    result = compute_reaction_time(
        target_activated_time=10.0,
        current_time=10.345,
    )

    assert result == 0.34500000000000064


def test_compute_reaction_time_never_returns_negative_value() -> None:
    result = compute_reaction_time(
        target_activated_time=10.0,
        current_time=9.0,
    )

    assert result == 0.0


def test_best_and_average_reaction_time_return_none_for_empty_list() -> None:
    assert compute_best_reaction_time([]) is None
    assert compute_average_reaction_time([]) is None


def test_best_and_average_reaction_time_return_values() -> None:
    reaction_times = [0.42, 0.31, 0.5]

    assert compute_best_reaction_time(reaction_times) == 0.31
    assert compute_average_reaction_time(reaction_times) == sum(reaction_times) / 3


def test_format_time_value_handles_none() -> None:
    assert format_time_value(None) == "--"


def test_format_time_value_formats_seconds() -> None:
    assert format_time_value(0.3456) == "0.346s"


def test_create_initial_state_schedules_first_target() -> None:
    rng = random.Random(123)

    state = create_initial_state(
        current_time=100.0,
        rng=rng,
        min_delay_seconds=1.0,
        max_delay_seconds=1.0,
    )

    assert state.start_time == 100.0
    assert state.phase == ReactionPhase.WAITING
    assert state.next_target_time == 101.0


def test_should_activate_target_returns_true_after_delay() -> None:
    state = create_initial_state(
        current_time=10.0,
        rng=random.Random(123),
        min_delay_seconds=1.0,
        max_delay_seconds=1.0,
    )

    assert should_activate_target(state=state, current_time=11.0)


def test_activate_target_sets_active_phase_and_time() -> None:
    state = create_initial_state(
        current_time=10.0,
        rng=random.Random(123),
        min_delay_seconds=1.0,
        max_delay_seconds=1.0,
    )

    activate_target(state=state, current_time=12.0)

    assert state.phase == ReactionPhase.TARGET_ACTIVE
    assert state.target_activated_time == 12.0


def test_is_successful_hit_requires_active_phase() -> None:
    assert not is_successful_hit(
        phase=ReactionPhase.WAITING,
        proximity_level=ProximityLevel.NEAR,
        last_hit_time=None,
        current_time=10.0,
    )


def test_is_successful_hit_accepts_near_level() -> None:
    assert is_successful_hit(
        phase=ReactionPhase.TARGET_ACTIVE,
        proximity_level=ProximityLevel.NEAR,
        last_hit_time=None,
        current_time=10.0,
    )


def test_is_successful_hit_rejects_far_level() -> None:
    assert not is_successful_hit(
        phase=ReactionPhase.TARGET_ACTIVE,
        proximity_level=ProximityLevel.SAFE,
        last_hit_time=None,
        current_time=10.0,
    )


def test_register_hit_updates_score_and_reaction_times() -> None:
    state = create_initial_state(
        current_time=10.0,
        rng=random.Random(123),
        min_delay_seconds=1.0,
        max_delay_seconds=1.0,
    )
    activate_target(state=state, current_time=12.0)

    reaction_time = register_hit(
        state=state,
        current_time=12.4,
        rng=random.Random(123),
        min_delay_seconds=1.0,
        max_delay_seconds=1.0,
    )

    assert reaction_time == 0.40000000000000036
    assert state.score == 1
    assert state.reaction_times == [0.40000000000000036]
    assert state.phase == ReactionPhase.WAITING
    assert state.target_activated_time is None
    assert state.next_target_time == 13.4


def test_finish_game_sets_finished_phase() -> None:
    state = create_initial_state(
        current_time=10.0,
        rng=random.Random(123),
        min_delay_seconds=1.0,
        max_delay_seconds=1.0,
    )

    finish_game(state)

    assert state.phase == ReactionPhase.FINISHED


def test_update_game_state_activates_target() -> None:
    state = create_initial_state(
        current_time=10.0,
        rng=random.Random(123),
        min_delay_seconds=1.0,
        max_delay_seconds=1.0,
    )

    update_game_state(
        state=state,
        proximity_level=ProximityLevel.SAFE,
        current_time=11.0,
        rng=random.Random(123),
        duration_seconds=30.0,
    )

    assert state.phase == ReactionPhase.TARGET_ACTIVE


def test_update_game_state_registers_hit() -> None:
    state = create_initial_state(
        current_time=10.0,
        rng=random.Random(123),
        min_delay_seconds=1.0,
        max_delay_seconds=1.0,
    )
    activate_target(state=state, current_time=11.0)

    reaction_time = update_game_state(
        state=state,
        proximity_level=ProximityLevel.NEAR,
        current_time=11.25,
        rng=random.Random(123),
        duration_seconds=30.0,
    )

    assert reaction_time == 0.25
    assert state.score == 1


def test_update_game_state_finishes_game_after_duration() -> None:
    state = create_initial_state(
        current_time=10.0,
        rng=random.Random(123),
        min_delay_seconds=1.0,
        max_delay_seconds=1.0,
    )

    update_game_state(
        state=state,
        proximity_level=ProximityLevel.NEAR,
        current_time=41.0,
        rng=random.Random(123),
        duration_seconds=30.0,
    )

    assert state.phase == ReactionPhase.FINISHED
