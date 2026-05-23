"""Reaction time game based on OAK-D stereo disparity."""

from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from enum import Enum

import cv2
import depthai as dai
import numpy as np

from oak_vision_lab.depth.camera import create_stereo_disparity_pipeline
from oak_vision_lab.depth.disparity import colorize_disparity_frame
from oak_vision_lab.depth.proximity import ProximityLevel, classify_proximity
from oak_vision_lab.game.timing import (
    get_time_left,
    has_cooldown_elapsed,
    is_timer_finished,
)

WINDOW_NAME = "oak-vision-lab | Reaction Time Game"

DEFAULT_GAME_DURATION_SECONDS = 30.0
DEFAULT_MIN_DELAY_SECONDS = 1.0
DEFAULT_MAX_DELAY_SECONDS = 3.5
DEFAULT_HIT_COOLDOWN_SECONDS = 0.8

TARGET_WIDTH_RATIO = 0.34
TARGET_HEIGHT_RATIO = 0.34

DEFAULT_NEAR_THRESHOLD = 25.0
DEFAULT_VERY_CLOSE_THRESHOLD = 45.0

SCORING_LEVELS = frozenset(
    {
        ProximityLevel.NEAR,
        ProximityLevel.VERY_CLOSE,
    },
)


class ReactionPhase(Enum):
    """Current phase of the reaction game."""

    WAITING = "waiting"
    TARGET_ACTIVE = "target_active"
    FINISHED = "finished"


@dataclass(frozen=True)
class TargetRegion:
    """Rectangular target region in image coordinates."""

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


@dataclass
class ReactionGameState:
    """Mutable game state for the reaction time game."""

    start_time: float
    phase: ReactionPhase
    next_target_time: float
    target_activated_time: float | None = None
    last_hit_time: float | None = None
    score: int = 0
    reaction_times: list[float] = field(default_factory=list)


def create_initial_state(
    *,
    current_time: float,
    rng: random.Random,
    min_delay_seconds: float = DEFAULT_MIN_DELAY_SECONDS,
    max_delay_seconds: float = DEFAULT_MAX_DELAY_SECONDS,
) -> ReactionGameState:
    """Create initial game state and schedule the first target."""

    return ReactionGameState(
        start_time=current_time,
        phase=ReactionPhase.WAITING,
        next_target_time=current_time
        + rng.uniform(min_delay_seconds, max_delay_seconds),
    )


def get_center_target_region(
    *,
    frame_width: int,
    frame_height: int,
    width_ratio: float = TARGET_WIDTH_RATIO,
    height_ratio: float = TARGET_HEIGHT_RATIO,
) -> TargetRegion:
    """Return a centered target region for the given frame size."""

    width = int(frame_width * width_ratio)
    height = int(frame_height * height_ratio)
    x = (frame_width - width) // 2
    y = (frame_height - height) // 2

    return TargetRegion(x=x, y=y, width=width, height=height)


def compute_region_mean_disparity(
    disparity_frame: np.ndarray,
    region: TargetRegion,
) -> float:
    """Compute mean disparity inside the target region."""

    roi = disparity_frame[region.y : region.y2, region.x : region.x2]

    if roi.size == 0:
        return 0.0

    valid_pixels = roi[roi > 0]

    if valid_pixels.size == 0:
        return 0.0

    return float(np.mean(valid_pixels))


def compute_reaction_time(
    *,
    target_activated_time: float,
    current_time: float,
) -> float:
    """Compute reaction time in seconds."""

    return max(0.0, current_time - target_activated_time)


def compute_best_reaction_time(reaction_times: list[float]) -> float | None:
    """Return the best reaction time or None when no hit exists."""

    if not reaction_times:
        return None

    return min(reaction_times)


def compute_average_reaction_time(reaction_times: list[float]) -> float | None:
    """Return the average reaction time or None when no hit exists."""

    if not reaction_times:
        return None

    return sum(reaction_times) / len(reaction_times)


def should_activate_target(
    *,
    state: ReactionGameState,
    current_time: float,
) -> bool:
    """Return True when the waiting target should become active."""

    return (
        state.phase == ReactionPhase.WAITING and current_time >= state.next_target_time
    )


def is_successful_hit(
    *,
    phase: ReactionPhase,
    proximity_level: ProximityLevel,
    last_hit_time: float | None,
    current_time: float,
    cooldown_seconds: float = DEFAULT_HIT_COOLDOWN_SECONDS,
) -> bool:
    """Return True when the current frame should count as a reaction hit."""

    if phase != ReactionPhase.TARGET_ACTIVE:
        return False

    if proximity_level not in SCORING_LEVELS:
        return False

    if last_hit_time is None:
        return True

    return has_cooldown_elapsed(
        last_event_time=last_hit_time,
        cooldown_seconds=cooldown_seconds,
        current_time=current_time,
    )


def activate_target(
    *,
    state: ReactionGameState,
    current_time: float,
) -> None:
    """Activate the current reaction target."""

    state.phase = ReactionPhase.TARGET_ACTIVE
    state.target_activated_time = current_time


def register_hit(
    *,
    state: ReactionGameState,
    current_time: float,
    rng: random.Random,
    min_delay_seconds: float = DEFAULT_MIN_DELAY_SECONDS,
    max_delay_seconds: float = DEFAULT_MAX_DELAY_SECONDS,
) -> float:
    """Register a successful hit and schedule the next target."""

    if state.target_activated_time is None:
        reaction_time = 0.0
    else:
        reaction_time = compute_reaction_time(
            target_activated_time=state.target_activated_time,
            current_time=current_time,
        )

    state.score += 1
    state.reaction_times.append(reaction_time)
    state.last_hit_time = current_time
    state.phase = ReactionPhase.WAITING
    state.target_activated_time = None
    state.next_target_time = current_time + rng.uniform(
        min_delay_seconds,
        max_delay_seconds,
    )

    return reaction_time


def finish_game(state: ReactionGameState) -> None:
    """Mark the game as finished."""

    state.phase = ReactionPhase.FINISHED


def format_time_value(value: float | None) -> str:
    """Format reaction time value for HUD output."""

    if value is None:
        return "--"

    return f"{value:.3f}s"


def draw_text(
    frame: np.ndarray,
    text: str,
    position: tuple[int, int],
    *,
    scale: float = 0.7,
    color: tuple[int, int, int] = (255, 255, 255),
    thickness: int = 2,
) -> None:
    """Draw readable text with a dark outline."""

    cv2.putText(
        frame,
        text,
        position,
        cv2.FONT_HERSHEY_SIMPLEX,
        scale,
        (0, 0, 0),
        thickness + 2,
        cv2.LINE_AA,
    )
    cv2.putText(
        frame,
        text,
        position,
        cv2.FONT_HERSHEY_SIMPLEX,
        scale,
        color,
        thickness,
        cv2.LINE_AA,
    )


def draw_target_region(
    frame: np.ndarray,
    region: TargetRegion,
    *,
    phase: ReactionPhase,
) -> None:
    """Draw the reaction target region."""

    if phase == ReactionPhase.TARGET_ACTIVE:
        color = (0, 255, 0)
        label = "HIT NOW!"
    elif phase == ReactionPhase.WAITING:
        color = (255, 180, 0)
        label = "WAIT..."
    else:
        color = (180, 180, 180)
        label = "FINISHED"

    cv2.rectangle(
        frame,
        (region.x, region.y),
        (region.x2, region.y2),
        color,
        3,
    )

    draw_text(
        frame,
        label,
        (region.x + 12, region.y + 34),
        scale=0.8,
        color=color,
        thickness=2,
    )


def draw_hud(
    frame: np.ndarray,
    *,
    state: ReactionGameState,
    time_left: float,
    mean_disparity: float,
    proximity_level: ProximityLevel,
) -> None:
    """Draw game HUD."""

    best_time = compute_best_reaction_time(state.reaction_times)
    average_time = compute_average_reaction_time(state.reaction_times)
    last_time = state.reaction_times[-1] if state.reaction_times else None

    lines = [
        "Reaction Time Game",
        f"Time left: {time_left:05.1f}s",
        f"Score: {state.score}",
        f"Phase: {state.phase.value}",
        f"Last: {format_time_value(last_time)}",
        f"Best: {format_time_value(best_time)}",
        f"Average: {format_time_value(average_time)}",
        f"Mean disparity: {mean_disparity:.1f}",
        f"Proximity: {proximity_level.value}",
        "R - restart | Q / ESC - quit",
    ]

    x = 20
    y = 34

    for index, line in enumerate(lines):
        draw_text(
            frame,
            line,
            (x, y + index * 28),
            scale=0.62,
            color=(255, 255, 255),
            thickness=1,
        )


def update_game_state(
    *,
    state: ReactionGameState,
    proximity_level: ProximityLevel,
    current_time: float,
    rng: random.Random,
    duration_seconds: float = DEFAULT_GAME_DURATION_SECONDS,
) -> float | None:
    """Update game state and return a new reaction time when a hit occurs."""

    if is_timer_finished(
        start_time=state.start_time,
        duration_seconds=duration_seconds,
        current_time=current_time,
    ):
        finish_game(state)
        return None

    if should_activate_target(state=state, current_time=current_time):
        activate_target(state=state, current_time=current_time)

    if is_successful_hit(
        phase=state.phase,
        proximity_level=proximity_level,
        last_hit_time=state.last_hit_time,
        current_time=current_time,
    ):
        return register_hit(
            state=state,
            current_time=current_time,
            rng=rng,
        )

    return None


def run() -> None:
    """Run the OAK-D reaction time game demo."""

    pipeline, max_disparity = create_stereo_disparity_pipeline()
    rng = random.Random()

    with dai.Device(pipeline) as device:
        disparity_queue = device.getOutputQueue(
            name="disparity",
            maxSize=4,
            blocking=False,
        )

        cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)

        current_time = time.monotonic()
        state = create_initial_state(current_time=current_time, rng=rng)

        while True:
            disparity_message = disparity_queue.get()
            disparity_frame = disparity_message.getFrame()

            frame_height, frame_width = disparity_frame.shape[:2]
            target_region = get_center_target_region(
                frame_width=frame_width,
                frame_height=frame_height,
            )

            mean_disparity = compute_region_mean_disparity(
                disparity_frame,
                target_region,
            )
            proximity_level = classify_proximity(
                mean_disparity=mean_disparity,
                near_threshold=DEFAULT_NEAR_THRESHOLD,
                very_close_threshold=DEFAULT_VERY_CLOSE_THRESHOLD,
            )

            current_time = time.monotonic()
            time_left = get_time_left(
                start_time=state.start_time,
                duration_seconds=DEFAULT_GAME_DURATION_SECONDS,
                current_time=current_time,
            )

            update_game_state(
                state=state,
                proximity_level=proximity_level,
                current_time=current_time,
                rng=rng,
            )

            display_frame = colorize_disparity_frame(
                disparity_frame,
                max_disparity=max_disparity,
            )

            draw_target_region(
                display_frame,
                target_region,
                phase=state.phase,
            )
            draw_hud(
                display_frame,
                state=state,
                time_left=time_left,
                mean_disparity=mean_disparity,
                proximity_level=proximity_level,
            )

            cv2.imshow(WINDOW_NAME, display_frame)

            key = cv2.waitKey(1) & 0xFF

            if key in {ord("q"), 27}:
                break

            if key == ord("r"):
                current_time = time.monotonic()
                state = create_initial_state(current_time=current_time, rng=rng)

    cv2.destroyWindow(WINDOW_NAME)


if __name__ == "__main__":
    run()
