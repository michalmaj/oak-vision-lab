import random

import numpy as np
import pytest

from oak_vision_lab.demos.depth_dodge_avoider_game import (
    DodgeGameState,
    DodgeZone,
    ZoneMeasurement,
    change_active_zone,
    choose_next_zone_index,
    compute_zone_mean_disparity,
    create_dodge_zones,
    create_initial_state,
    detect_collision,
    get_dodge_message,
    has_collision_cooldown_elapsed,
    is_zone_occupied,
    register_collision,
    update_dodge_game,
)
from oak_vision_lab.depth.proximity import ProximityLevel


def test_create_dodge_zones_returns_expected_number_of_zones() -> None:
    zones = create_dodge_zones(
        frame_width=100,
        frame_height=80,
        zone_count=4,
    )

    assert len(zones) == 4
    assert zones[0].label == "Zone 1"
    assert zones[-1].label == "Zone 4"


def test_create_dodge_zones_covers_frame_width_with_remainder() -> None:
    zones = create_dodge_zones(
        frame_width=103,
        frame_height=80,
        zone_count=4,
    )

    assert zones[0] == DodgeZone(
        index=0, label="Zone 1", x=0, y=17, width=25, height=52
    )
    assert zones[-1].x2 == 103


def test_create_dodge_zones_rejects_invalid_frame_dimensions() -> None:
    with pytest.raises(ValueError, match="frame dimensions must be positive"):
        create_dodge_zones(frame_width=0, frame_height=80)


def test_create_dodge_zones_rejects_invalid_zone_count() -> None:
    with pytest.raises(ValueError, match="zone_count must be positive"):
        create_dodge_zones(frame_width=100, frame_height=80, zone_count=0)


def test_create_dodge_zones_rejects_invalid_usable_height() -> None:
    with pytest.raises(ValueError, match="usable zone height must be positive"):
        create_dodge_zones(
            frame_width=100,
            frame_height=80,
            top_margin_ratio=0.9,
            bottom_margin_ratio=0.2,
        )


def test_compute_zone_mean_disparity_ignores_zero_values() -> None:
    frame = np.array(
        [
            [0, 0, 0, 0],
            [0, 10, 20, 0],
            [0, 30, 40, 0],
            [0, 0, 0, 0],
        ],
        dtype=np.uint8,
    )
    zone = DodgeZone(index=0, label="Zone 1", x=1, y=1, width=2, height=2)

    result = compute_zone_mean_disparity(frame, zone)

    assert result == 25.0


def test_compute_zone_mean_disparity_returns_zero_without_valid_pixels() -> None:
    frame = np.zeros((4, 4), dtype=np.uint8)
    zone = DodgeZone(index=0, label="Zone 1", x=1, y=1, width=2, height=2)

    result = compute_zone_mean_disparity(frame, zone)

    assert result == 0.0


def test_is_zone_occupied_returns_true_for_near_and_very_close() -> None:
    assert is_zone_occupied(ProximityLevel.NEAR)
    assert is_zone_occupied(ProximityLevel.VERY_CLOSE)


def test_is_zone_occupied_returns_false_for_safe() -> None:
    assert not is_zone_occupied(ProximityLevel.SAFE)


def test_has_collision_cooldown_elapsed_allows_first_collision() -> None:
    result = has_collision_cooldown_elapsed(
        last_collision_time=None,
        current_time=10.0,
    )

    assert result


def test_has_collision_cooldown_elapsed_rejects_collision_inside_cooldown() -> None:
    result = has_collision_cooldown_elapsed(
        last_collision_time=10.0,
        current_time=10.2,
        cooldown_seconds=0.8,
    )

    assert not result


def test_has_collision_cooldown_elapsed_allows_collision_after_cooldown() -> None:
    result = has_collision_cooldown_elapsed(
        last_collision_time=10.0,
        current_time=10.9,
        cooldown_seconds=0.8,
    )

    assert result


def test_has_collision_cooldown_elapsed_rejects_negative_cooldown() -> None:
    with pytest.raises(ValueError, match="cooldown_seconds must be non-negative"):
        has_collision_cooldown_elapsed(
            last_collision_time=None,
            current_time=10.0,
            cooldown_seconds=-1.0,
        )


def test_detect_collision_returns_true_when_active_zone_is_occupied() -> None:
    zones = create_dodge_zones(frame_width=100, frame_height=80, zone_count=2)
    measurements = [
        ZoneMeasurement(
            zone=zones[0],
            mean_disparity=0.0,
            proximity_level=ProximityLevel.SAFE,
            occupied=False,
        ),
        ZoneMeasurement(
            zone=zones[1],
            mean_disparity=50.0,
            proximity_level=ProximityLevel.VERY_CLOSE,
            occupied=True,
        ),
    ]

    assert detect_collision(measurements=measurements, active_zone_index=1)


def test_detect_collision_returns_false_when_active_zone_is_empty() -> None:
    zones = create_dodge_zones(frame_width=100, frame_height=80, zone_count=2)
    measurements = [
        ZoneMeasurement(
            zone=zones[0],
            mean_disparity=50.0,
            proximity_level=ProximityLevel.VERY_CLOSE,
            occupied=True,
        ),
        ZoneMeasurement(
            zone=zones[1],
            mean_disparity=0.0,
            proximity_level=ProximityLevel.SAFE,
            occupied=False,
        ),
    ]

    assert not detect_collision(measurements=measurements, active_zone_index=1)


def test_choose_next_zone_index_returns_zero_for_single_zone() -> None:
    result = choose_next_zone_index(
        current_zone_index=0,
        zone_count=1,
        rng=random.Random(123),
    )

    assert result == 0


def test_choose_next_zone_index_rejects_invalid_zone_count() -> None:
    with pytest.raises(ValueError, match="zone_count must be positive"):
        choose_next_zone_index(
            current_zone_index=0,
            zone_count=0,
            rng=random.Random(123),
        )


def test_choose_next_zone_index_avoids_current_zone_when_possible() -> None:
    result = choose_next_zone_index(
        current_zone_index=1,
        zone_count=4,
        rng=random.Random(123),
    )

    assert result != 1
    assert 0 <= result < 4


def test_create_initial_state_returns_valid_state() -> None:
    state = create_initial_state(
        current_time=10.0,
        rng=random.Random(123),
        zone_count=4,
        zone_change_seconds=1.4,
        lives=3,
    )

    assert 0 <= state.active_zone_index < 4
    assert state.next_zone_change_time == 11.4
    assert state.lives == 3
    assert not state.game_over


def test_create_initial_state_rejects_invalid_zone_count() -> None:
    with pytest.raises(ValueError, match="zone_count must be positive"):
        create_initial_state(
            current_time=10.0,
            rng=random.Random(123),
            zone_count=0,
        )


def test_create_initial_state_rejects_invalid_zone_change_seconds() -> None:
    with pytest.raises(ValueError, match="zone_change_seconds must be positive"):
        create_initial_state(
            current_time=10.0,
            rng=random.Random(123),
            zone_change_seconds=0.0,
        )


def test_create_initial_state_rejects_invalid_lives() -> None:
    with pytest.raises(ValueError, match="lives must be positive"):
        create_initial_state(
            current_time=10.0,
            rng=random.Random(123),
            lives=0,
        )


def test_change_active_zone_awards_score_by_default() -> None:
    state = DodgeGameState(
        active_zone_index=0,
        next_zone_change_time=11.0,
        score=2,
        lives=3,
    )

    updated = change_active_zone(
        state=state,
        current_time=12.0,
        rng=random.Random(123),
        zone_count=4,
        zone_change_seconds=1.5,
    )

    assert updated.active_zone_index != 0
    assert updated.next_zone_change_time == 13.5
    assert updated.score == 3


def test_change_active_zone_can_skip_score_award() -> None:
    state = DodgeGameState(
        active_zone_index=0,
        next_zone_change_time=11.0,
        score=2,
        lives=3,
    )

    updated = change_active_zone(
        state=state,
        current_time=12.0,
        rng=random.Random(123),
        zone_count=4,
        zone_change_seconds=1.5,
        award_score=False,
    )

    assert updated.score == 2


def test_register_collision_decreases_lives() -> None:
    state = DodgeGameState(
        active_zone_index=0,
        next_zone_change_time=11.0,
        lives=3,
    )

    updated = register_collision(
        state=state,
        current_time=12.0,
    )

    assert updated.lives == 2
    assert updated.collisions == 1
    assert updated.last_collision_time == 12.0
    assert not updated.game_over


def test_register_collision_sets_game_over_when_lives_reach_zero() -> None:
    state = DodgeGameState(
        active_zone_index=0,
        next_zone_change_time=11.0,
        lives=1,
    )

    updated = register_collision(
        state=state,
        current_time=12.0,
    )

    assert updated.lives == 0
    assert updated.game_over


def test_update_dodge_game_returns_same_state_when_game_is_over() -> None:
    state = DodgeGameState(
        active_zone_index=0,
        next_zone_change_time=11.0,
        game_over=True,
    )

    result = update_dodge_game(
        state=state,
        measurements=[],
        current_time=12.0,
        rng=random.Random(123),
    )

    assert result.state == state
    assert not result.collision
    assert not result.zone_changed


def test_update_dodge_game_awards_score_when_zone_changes_without_collision() -> None:
    state = DodgeGameState(
        active_zone_index=0,
        next_zone_change_time=11.0,
        score=0,
        lives=3,
    )

    result = update_dodge_game(
        state=state,
        measurements=[],
        current_time=11.0,
        rng=random.Random(123),
        zone_count=4,
        zone_change_seconds=1.4,
    )

    assert result.zone_changed
    assert result.score_awarded
    assert result.state.score == 1


def test_update_dodge_game_registers_collision_and_changes_zone() -> None:
    zone = DodgeZone(index=0, label="Zone 1", x=0, y=0, width=10, height=10)
    state = DodgeGameState(
        active_zone_index=0,
        next_zone_change_time=20.0,
        lives=3,
    )
    measurements = [
        ZoneMeasurement(
            zone=zone,
            mean_disparity=50.0,
            proximity_level=ProximityLevel.VERY_CLOSE,
            occupied=True,
        ),
    ]

    result = update_dodge_game(
        state=state,
        measurements=measurements,
        current_time=12.0,
        rng=random.Random(123),
        zone_count=4,
    )

    assert result.collision
    assert result.zone_changed
    assert not result.score_awarded
    assert result.state.lives == 2
    assert result.state.collisions == 1


def test_update_dodge_game_ignores_collision_inside_cooldown() -> None:
    zone = DodgeZone(index=0, label="Zone 1", x=0, y=0, width=10, height=10)
    state = DodgeGameState(
        active_zone_index=0,
        next_zone_change_time=20.0,
        lives=3,
        last_collision_time=11.8,
    )
    measurements = [
        ZoneMeasurement(
            zone=zone,
            mean_disparity=50.0,
            proximity_level=ProximityLevel.VERY_CLOSE,
            occupied=True,
        ),
    ]

    result = update_dodge_game(
        state=state,
        measurements=measurements,
        current_time=12.0,
        rng=random.Random(123),
        collision_cooldown_seconds=0.8,
    )

    assert not result.collision
    assert result.state.lives == 3


def test_update_dodge_game_sets_game_over_after_last_life_collision() -> None:
    zone = DodgeZone(index=0, label="Zone 1", x=0, y=0, width=10, height=10)
    state = DodgeGameState(
        active_zone_index=0,
        next_zone_change_time=20.0,
        lives=1,
    )
    measurements = [
        ZoneMeasurement(
            zone=zone,
            mean_disparity=50.0,
            proximity_level=ProximityLevel.VERY_CLOSE,
            occupied=True,
        ),
    ]

    result = update_dodge_game(
        state=state,
        measurements=measurements,
        current_time=12.0,
        rng=random.Random(123),
    )

    assert result.collision
    assert result.state.game_over
    assert result.state.lives == 0


def test_get_dodge_message_returns_game_over_message() -> None:
    state = DodgeGameState(
        active_zone_index=0,
        next_zone_change_time=10.0,
        game_over=True,
    )

    message = get_dodge_message(
        collision=False,
        score_awarded=False,
        state=state,
    )

    assert "Game over" in message


def test_get_dodge_message_returns_collision_message() -> None:
    state = DodgeGameState(
        active_zone_index=0,
        next_zone_change_time=10.0,
    )

    message = get_dodge_message(
        collision=True,
        score_awarded=False,
        state=state,
    )

    assert "Collision" in message


def test_get_dodge_message_returns_score_message() -> None:
    state = DodgeGameState(
        active_zone_index=0,
        next_zone_change_time=10.0,
    )

    message = get_dodge_message(
        collision=False,
        score_awarded=True,
        state=state,
    )

    assert "Nice dodge" in message


def test_get_dodge_message_returns_default_instruction() -> None:
    state = DodgeGameState(
        active_zone_index=0,
        next_zone_change_time=10.0,
    )

    message = get_dodge_message(
        collision=False,
        score_awarded=False,
        state=state,
    )

    assert "Stay away" in message
