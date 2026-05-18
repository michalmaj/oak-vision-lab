"""Reusable game timing helpers."""

from __future__ import annotations


def get_time_left(
    *,
    start_time: float,
    duration_seconds: float,
    current_time: float,
) -> float:
    """Return remaining time in seconds."""

    if duration_seconds < 0.0:
        msg = "duration_seconds must be non-negative"
        raise ValueError(msg)

    elapsed_time = current_time - start_time

    return max(0.0, duration_seconds - elapsed_time)


def is_timer_finished(
    *,
    start_time: float,
    duration_seconds: float,
    current_time: float,
) -> bool:
    """Check whether a countdown timer has finished."""

    return (
        get_time_left(
            start_time=start_time,
            duration_seconds=duration_seconds,
            current_time=current_time,
        )
        <= 0.0
    )


def has_cooldown_elapsed(
    *,
    last_event_time: float,
    cooldown_seconds: float,
    current_time: float,
) -> bool:
    """Check whether enough time has passed since the previous event."""

    if cooldown_seconds < 0.0:
        msg = "cooldown_seconds must be non-negative"
        raise ValueError(msg)

    return current_time - last_event_time >= cooldown_seconds
