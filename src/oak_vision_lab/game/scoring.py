"""Reusable game scoring helpers."""

from __future__ import annotations

from collections.abc import Container
from enum import Enum

from oak_vision_lab.game.timing import has_cooldown_elapsed


def is_scoring_level(
    level: Enum,
    scoring_levels: Container[Enum],
) -> bool:
    """Check whether the current level should be treated as a scoring level."""

    return level in scoring_levels


def should_award_points(
    *,
    level: Enum,
    scoring_levels: Container[Enum],
    is_finished: bool,
    last_hit_time: float,
    cooldown_seconds: float,
    current_time: float,
) -> bool:
    """Check whether points should be awarded."""

    if is_finished:
        return False

    if not is_scoring_level(level, scoring_levels):
        return False

    return has_cooldown_elapsed(
        last_event_time=last_hit_time,
        cooldown_seconds=cooldown_seconds,
        current_time=current_time,
    )


def add_points(
    *,
    current_score: int,
    points: int,
) -> int:
    """Return a new score after adding points."""

    if points < 0:
        msg = "points must be non-negative"
        raise ValueError(msg)

    return current_score + points
