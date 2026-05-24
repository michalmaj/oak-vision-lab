"""Depth dodge / avoider game logic based on stereo disparity zones."""

from __future__ import annotations

import random
from dataclasses import dataclass

import numpy as np

from oak_vision_lab.depth.proximity import ProximityLevel

DEFAULT_ZONE_COUNT = 4
DEFAULT_LIVES = 3
DEFAULT_ZONE_CHANGE_SECONDS = 1.4
DEFAULT_COLLISION_COOLDOWN_SECONDS = 0.8

DEFAULT_NEAR_THRESHOLD = 25.0
DEFAULT_VERY_CLOSE_THRESHOLD = 45.0


@dataclass(frozen=True)
class DodgeZone:
    """Rectangular dodge zone in image coordinates."""

    index: int
    label: str
    x: int
    y: int
    width: int
    height: int

    @property
    def x2(self) -> int:
        """Return the right edge coordinate."""

        return self.x + self.width

    @property
    def y2(self) -> int:
        """Return the bottom edge coordinate."""

        return self.y + self.height


@dataclass(frozen=True)
class ZoneMeasurement:
    """Measurement result for a single dodge zone."""

    zone: DodgeZone
    mean_disparity: float
    proximity_level: ProximityLevel
    occupied: bool


@dataclass(frozen=True)
class DodgeGameState:
    """State of the depth dodge / avoider game."""

    active_zone_index: int
    next_zone_change_time: float
    score: int = 0
    lives: int = DEFAULT_LIVES
    collisions: int = 0
    last_collision_time: float | None = None
    game_over: bool = False


@dataclass(frozen=True)
class DodgeUpdateResult:
    """Result of a single dodge game update."""

    state: DodgeGameState
    collision: bool
    zone_changed: bool
    score_awarded: bool


def create_dodge_zones(
    *,
    frame_width: int,
    frame_height: int,
    zone_count: int = DEFAULT_ZONE_COUNT,
    top_margin_ratio: float = 0.22,
    bottom_margin_ratio: float = 0.12,
) -> list[DodgeZone]:
    """Create horizontal dodge zones across the frame."""

    if frame_width <= 0 or frame_height <= 0:
        msg = "frame dimensions must be positive"
        raise ValueError(msg)

    if zone_count <= 0:
        msg = "zone_count must be positive"
        raise ValueError(msg)

    usable_y = int(frame_height * top_margin_ratio)
    usable_height = int(frame_height * (1.0 - top_margin_ratio - bottom_margin_ratio))

    if usable_height <= 0:
        msg = "usable zone height must be positive"
        raise ValueError(msg)

    zone_width = frame_width // zone_count
    zones: list[DodgeZone] = []

    for index in range(zone_count):
        x = index * zone_width

        width = frame_width - x if index == zone_count - 1 else zone_width

        zones.append(
            DodgeZone(
                index=index,
                label=f"Zone {index + 1}",
                x=x,
                y=usable_y,
                width=width,
                height=usable_height,
            ),
        )

    return zones


def compute_zone_mean_disparity(
    disparity_frame: np.ndarray,
    zone: DodgeZone,
) -> float:
    """Compute mean non-zero disparity inside a dodge zone."""

    roi = disparity_frame[zone.y : zone.y2, zone.x : zone.x2]

    if roi.size == 0:
        return 0.0

    valid_pixels = roi[roi > 0]

    if valid_pixels.size == 0:
        return 0.0

    return float(np.mean(valid_pixels))


def is_zone_occupied(proximity_level: ProximityLevel) -> bool:
    """Return True when a zone contains a close object."""

    return proximity_level in {
        ProximityLevel.NEAR,
        ProximityLevel.VERY_CLOSE,
    }


def has_collision_cooldown_elapsed(
    *,
    last_collision_time: float | None,
    current_time: float,
    cooldown_seconds: float = DEFAULT_COLLISION_COOLDOWN_SECONDS,
) -> bool:
    """Return True when another collision can be registered."""

    if cooldown_seconds < 0.0:
        msg = "cooldown_seconds must be non-negative"
        raise ValueError(msg)

    if last_collision_time is None:
        return True

    return current_time - last_collision_time >= cooldown_seconds


def detect_collision(
    *,
    measurements: list[ZoneMeasurement],
    active_zone_index: int,
) -> bool:
    """Return True when the active danger zone is occupied."""

    for measurement in measurements:
        if measurement.zone.index != active_zone_index:
            continue

        return measurement.occupied

    return False


def choose_next_zone_index(
    *,
    current_zone_index: int,
    zone_count: int,
    rng: random.Random,
) -> int:
    """Choose a new active zone index different from the current one when possible."""

    if zone_count <= 0:
        msg = "zone_count must be positive"
        raise ValueError(msg)

    if zone_count == 1:
        return 0

    candidates = [
        zone_index
        for zone_index in range(zone_count)
        if zone_index != current_zone_index
    ]

    return rng.choice(candidates)


def create_initial_state(
    *,
    current_time: float,
    rng: random.Random,
    zone_count: int = DEFAULT_ZONE_COUNT,
    zone_change_seconds: float = DEFAULT_ZONE_CHANGE_SECONDS,
    lives: int = DEFAULT_LIVES,
) -> DodgeGameState:
    """Create initial dodge game state."""

    if zone_count <= 0:
        msg = "zone_count must be positive"
        raise ValueError(msg)

    if zone_change_seconds <= 0.0:
        msg = "zone_change_seconds must be positive"
        raise ValueError(msg)

    if lives <= 0:
        msg = "lives must be positive"
        raise ValueError(msg)

    return DodgeGameState(
        active_zone_index=rng.randrange(zone_count),
        next_zone_change_time=current_time + zone_change_seconds,
        lives=lives,
    )


def change_active_zone(
    *,
    state: DodgeGameState,
    current_time: float,
    rng: random.Random,
    zone_count: int = DEFAULT_ZONE_COUNT,
    zone_change_seconds: float = DEFAULT_ZONE_CHANGE_SECONDS,
    award_score: bool = True,
) -> DodgeGameState:
    """Return state with a new active danger zone."""

    next_zone_index = choose_next_zone_index(
        current_zone_index=state.active_zone_index,
        zone_count=zone_count,
        rng=rng,
    )

    score = state.score + int(award_score)

    return DodgeGameState(
        active_zone_index=next_zone_index,
        next_zone_change_time=current_time + zone_change_seconds,
        score=score,
        lives=state.lives,
        collisions=state.collisions,
        last_collision_time=state.last_collision_time,
        game_over=state.game_over,
    )


def register_collision(
    *,
    state: DodgeGameState,
    current_time: float,
) -> DodgeGameState:
    """Return state after a collision."""

    lives = max(0, state.lives - 1)
    game_over = lives == 0

    return DodgeGameState(
        active_zone_index=state.active_zone_index,
        next_zone_change_time=state.next_zone_change_time,
        score=state.score,
        lives=lives,
        collisions=state.collisions + 1,
        last_collision_time=current_time,
        game_over=game_over,
    )


def update_dodge_game(
    *,
    state: DodgeGameState,
    measurements: list[ZoneMeasurement],
    current_time: float,
    rng: random.Random,
    zone_count: int = DEFAULT_ZONE_COUNT,
    zone_change_seconds: float = DEFAULT_ZONE_CHANGE_SECONDS,
    collision_cooldown_seconds: float = DEFAULT_COLLISION_COOLDOWN_SECONDS,
) -> DodgeUpdateResult:
    """Update dodge game state from current zone measurements."""

    if state.game_over:
        return DodgeUpdateResult(
            state=state,
            collision=False,
            zone_changed=False,
            score_awarded=False,
        )

    collision = detect_collision(
        measurements=measurements,
        active_zone_index=state.active_zone_index,
    )

    if collision and has_collision_cooldown_elapsed(
        last_collision_time=state.last_collision_time,
        current_time=current_time,
        cooldown_seconds=collision_cooldown_seconds,
    ):
        collided_state = register_collision(
            state=state,
            current_time=current_time,
        )

        if collided_state.game_over:
            return DodgeUpdateResult(
                state=collided_state,
                collision=True,
                zone_changed=False,
                score_awarded=False,
            )

        changed_state = change_active_zone(
            state=collided_state,
            current_time=current_time,
            rng=rng,
            zone_count=zone_count,
            zone_change_seconds=zone_change_seconds,
            award_score=False,
        )

        return DodgeUpdateResult(
            state=changed_state,
            collision=True,
            zone_changed=True,
            score_awarded=False,
        )

    if current_time >= state.next_zone_change_time:
        changed_state = change_active_zone(
            state=state,
            current_time=current_time,
            rng=rng,
            zone_count=zone_count,
            zone_change_seconds=zone_change_seconds,
            award_score=True,
        )

        return DodgeUpdateResult(
            state=changed_state,
            collision=False,
            zone_changed=True,
            score_awarded=True,
        )

    return DodgeUpdateResult(
        state=state,
        collision=False,
        zone_changed=False,
        score_awarded=False,
    )


def get_dodge_message(
    *,
    collision: bool,
    score_awarded: bool,
    state: DodgeGameState,
) -> str:
    """Return a short HUD message for the dodge game."""

    if state.game_over:
        return "Game over. Press R to restart."

    if collision:
        return "Collision! Avoid the danger zone."

    if score_awarded:
        return "Nice dodge! Score awarded."

    return "Stay away from the highlighted danger zone."
