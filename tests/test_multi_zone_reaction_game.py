import random

import numpy as np
import pytest

from oak_vision_lab.demos.multi_zone_reaction_game import (
    MultiZoneReactionGameConfig,
    ReactionZone,
    create_default_zones,
    create_initial_game_state,
    extract_zone_roi,
    get_time_left,
    get_zone_bounds,
    is_game_finished,
    select_next_zone_index,
    should_award_points,
    update_game_state,
    validate_active_zone_index,
    validate_zone,
)
from oak_vision_lab.depth.proximity import ProximityLevel


def test_validate_zone_accepts_valid_zone() -> None:
    zone = ReactionZone(label="A", center_x=0.5, center_y=0.5, scale=0.2)

    validate_zone(zone)


def test_validate_zone_rejects_empty_label() -> None:
    zone = ReactionZone(label="", center_x=0.5, center_y=0.5, scale=0.2)

    with pytest.raises(ValueError, match="zone label must not be empty"):
        validate_zone(zone)


def test_create_default_zones_returns_four_zones() -> None:
    zones = create_default_zones(zone_scale=0.22)

    assert len(zones) == 4
    assert [zone.label for zone in zones] == ["A", "B", "C", "D"]


def test_validate_active_zone_index_rejects_empty_zone_list() -> None:
    with pytest.raises(ValueError, match="zone_count must be greater than zero"):
        validate_active_zone_index(active_zone_index=0, zone_count=0)


def test_validate_active_zone_index_rejects_out_of_range_index() -> None:
    with pytest.raises(ValueError, match="active_zone_index must point"):
        validate_active_zone_index(active_zone_index=4, zone_count=4)


def test_select_next_zone_index_does_not_return_current_index() -> None:
    rng = random.Random(123)

    next_index = select_next_zone_index(
        rng,
        zone_count=4,
        current_index=1,
    )

    assert next_index != 1
    assert 0 <= next_index < 4


def test_select_next_zone_index_returns_same_index_for_single_zone() -> None:
    rng = random.Random(123)

    next_index = select_next_zone_index(
        rng,
        zone_count=1,
        current_index=0,
    )

    assert next_index == 0


def test_create_initial_game_state_sets_initial_values() -> None:
    state = create_initial_game_state(
        current_time=100.0,
        active_zone_index=2,
        zone_count=4,
    )

    assert state.score == 0
    assert state.start_time == 100.0
    assert state.last_hit_time == float("-inf")
    assert state.active_zone_index == 2


def test_get_time_left_returns_remaining_time() -> None:
    config = MultiZoneReactionGameConfig(duration_seconds=30.0)
    state = create_initial_game_state(
        current_time=100.0,
        active_zone_index=0,
        zone_count=4,
    )

    time_left = get_time_left(state, config, current_time=112.5)

    assert time_left == 17.5


def test_is_game_finished_returns_true_after_duration() -> None:
    config = MultiZoneReactionGameConfig(duration_seconds=30.0)
    state = create_initial_game_state(
        current_time=100.0,
        active_zone_index=0,
        zone_count=4,
    )

    assert is_game_finished(state, config, current_time=130.0)


def test_get_zone_bounds_returns_expected_bounds() -> None:
    zone = ReactionZone(label="A", center_x=0.5, center_y=0.5, scale=0.25)

    bounds = get_zone_bounds((100, 200), zone)

    assert bounds == (75, 38, 125, 63)


def test_extract_zone_roi_returns_expected_shape() -> None:
    frame = np.zeros((100, 200), dtype=np.uint8)
    zone = ReactionZone(label="A", center_x=0.5, center_y=0.5, scale=0.5)

    roi = extract_zone_roi(frame, zone)

    assert roi.shape == (50, 100)


def test_should_award_points_for_near_level() -> None:
    config = MultiZoneReactionGameConfig(hit_cooldown_seconds=0.35)
    state = create_initial_game_state(
        current_time=100.0,
        active_zone_index=0,
        zone_count=4,
    )

    result = should_award_points(
        ProximityLevel.NEAR,
        state,
        config,
        current_time=100.1,
    )

    assert result


def test_should_not_award_points_for_safe_level() -> None:
    config = MultiZoneReactionGameConfig()
    state = create_initial_game_state(
        current_time=100.0,
        active_zone_index=0,
        zone_count=4,
    )

    result = should_award_points(
        ProximityLevel.SAFE,
        state,
        config,
        current_time=100.1,
    )

    assert not result


def test_update_game_state_awards_points_and_changes_active_zone() -> None:
    config = MultiZoneReactionGameConfig(points_per_hit=10)
    state = create_initial_game_state(
        current_time=100.0,
        active_zone_index=0,
        zone_count=4,
    )

    updated_state, points_awarded = update_game_state(
        ProximityLevel.VERY_CLOSE,
        state,
        config,
        current_time=100.1,
        next_zone_index=2,
        zone_count=4,
    )

    assert points_awarded
    assert updated_state.score == 10
    assert updated_state.last_hit_time == 100.1
    assert updated_state.active_zone_index == 2


def test_update_game_state_does_not_award_points_after_game_finished() -> None:
    config = MultiZoneReactionGameConfig(duration_seconds=30.0)
    state = create_initial_game_state(
        current_time=100.0,
        active_zone_index=0,
        zone_count=4,
    )

    updated_state, points_awarded = update_game_state(
        ProximityLevel.VERY_CLOSE,
        state,
        config,
        current_time=131.0,
        next_zone_index=2,
        zone_count=4,
    )

    assert not points_awarded
    assert updated_state == state
