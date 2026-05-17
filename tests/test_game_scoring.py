from enum import Enum

import pytest

from oak_vision_lab.game.scoring import (
    add_points,
    is_scoring_level,
    should_award_points,
)


class ExampleLevel(Enum):
    SAFE = "SAFE"
    NEAR = "NEAR"
    VERY_CLOSE = "VERY CLOSE"


SCORING_LEVELS = {
    ExampleLevel.NEAR,
    ExampleLevel.VERY_CLOSE,
}


def test_is_scoring_level_returns_true_for_scoring_level() -> None:
    assert is_scoring_level(ExampleLevel.NEAR, SCORING_LEVELS)


def test_is_scoring_level_returns_false_for_non_scoring_level() -> None:
    assert not is_scoring_level(ExampleLevel.SAFE, SCORING_LEVELS)


def test_should_award_points_returns_true_for_scoring_level_after_cooldown() -> None:
    result = should_award_points(
        level=ExampleLevel.NEAR,
        scoring_levels=SCORING_LEVELS,
        is_finished=False,
        last_hit_time=100.0,
        cooldown_seconds=0.35,
        current_time=100.35,
    )

    assert not result


def test_should_award_points_returns_false_when_game_is_finished() -> None:
    result = should_award_points(
        level=ExampleLevel.NEAR,
        scoring_levels=SCORING_LEVELS,
        is_finished=True,
        last_hit_time=100.0,
        cooldown_seconds=0.35,
        current_time=101.0,
    )

    assert not result


def test_should_award_points_returns_false_for_non_scoring_level() -> None:
    result = should_award_points(
        level=ExampleLevel.SAFE,
        scoring_levels=SCORING_LEVELS,
        is_finished=False,
        last_hit_time=100.0,
        cooldown_seconds=0.35,
        current_time=101.0,
    )

    assert not result


def test_should_award_points_returns_false_during_cooldown() -> None:
    result = should_award_points(
        level=ExampleLevel.NEAR,
        scoring_levels=SCORING_LEVELS,
        is_finished=False,
        last_hit_time=100.0,
        cooldown_seconds=0.35,
        current_time=100.2,
    )

    assert not result


def test_add_points_returns_updated_score() -> None:
    assert add_points(current_score=20, points=10) == 30


def test_add_points_rejects_negative_points() -> None:
    with pytest.raises(ValueError, match="points must be non-negative"):
        add_points(current_score=20, points=-10)
