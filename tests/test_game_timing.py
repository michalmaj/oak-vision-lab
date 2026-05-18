import pytest

from oak_vision_lab.game.timing import (
    get_time_left,
    has_cooldown_elapsed,
    is_timer_finished,
)


def test_get_time_left_returns_remaining_time() -> None:
    time_left = get_time_left(
        start_time=100.0,
        duration_seconds=30.0,
        current_time=112.5,
    )

    assert time_left == 17.5


def test_get_time_left_does_not_return_negative_values() -> None:
    time_left = get_time_left(
        start_time=100.0,
        duration_seconds=30.0,
        current_time=200.0,
    )

    assert time_left == 0.0


def test_get_time_left_rejects_negative_duration() -> None:
    with pytest.raises(ValueError, match="duration_seconds must be non-negative"):
        get_time_left(
            start_time=100.0,
            duration_seconds=-1.0,
            current_time=101.0,
        )


def test_is_timer_finished_returns_false_before_duration() -> None:
    result = is_timer_finished(
        start_time=100.0,
        duration_seconds=30.0,
        current_time=129.9,
    )

    assert not result


def test_is_timer_finished_returns_true_after_duration() -> None:
    result = is_timer_finished(
        start_time=100.0,
        duration_seconds=30.0,
        current_time=130.0,
    )

    assert result


def test_has_cooldown_elapsed_returns_true_after_cooldown() -> None:
    result = has_cooldown_elapsed(
        last_event_time=100.0,
        cooldown_seconds=0.35,
        current_time=100.35,
    )

    assert not result


def test_has_cooldown_elapsed_returns_false_during_cooldown() -> None:
    result = has_cooldown_elapsed(
        last_event_time=100.0,
        cooldown_seconds=0.35,
        current_time=100.2,
    )

    assert not result


def test_has_cooldown_elapsed_rejects_negative_cooldown() -> None:
    with pytest.raises(ValueError, match="cooldown_seconds must be non-negative"):
        has_cooldown_elapsed(
            last_event_time=100.0,
            cooldown_seconds=-1.0,
            current_time=101.0,
        )
