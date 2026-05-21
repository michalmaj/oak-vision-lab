"""OAK-D multi-zone reaction game demo using DepthAI v2 API."""

from __future__ import annotations

import random
import time
from dataclasses import dataclass, replace

import cv2
import depthai as dai
import numpy as np
from numpy.typing import NDArray

from oak_vision_lab.depth.camera import create_stereo_disparity_pipeline
from oak_vision_lab.depth.disparity import (
    colorize_disparity_frame,
    compute_mean_disparity,
)
from oak_vision_lab.depth.proximity import (
    ProximityLevel,
    classify_proximity,
    get_alert_color,
)
from oak_vision_lab.game.scoring import (
    add_points,
    is_scoring_level,
)
from oak_vision_lab.game.scoring import (
    should_award_points as should_award_scoring_points,
)
from oak_vision_lab.game.timing import (
    get_time_left as get_timer_time_left,
)
from oak_vision_lab.game.timing import (
    is_timer_finished,
)
from oak_vision_lab.visualization.hud import HudConfig, build_hud_lines


@dataclass(frozen=True)
class ReactionZone:
    """A reaction zone described with normalized center coordinates."""

    label: str
    center_x: float
    center_y: float
    scale: float = 0.22


@dataclass(frozen=True)
class MultiZoneReactionGameConfig:
    """Configuration for the multi-zone reaction game."""

    duration_seconds: float = 30.0
    hit_cooldown_seconds: float = 0.35
    points_per_hit: int = 10
    near_threshold: float = 25.0
    very_close_threshold: float = 45.0
    zone_scale: float = 0.22


@dataclass(frozen=True)
class MultiZoneReactionGameState:
    """Current state of the multi-zone reaction game."""

    score: int
    start_time: float
    last_hit_time: float
    active_zone_index: int


SCORING_PROXIMITY_LEVELS = {
    ProximityLevel.NEAR,
    ProximityLevel.VERY_CLOSE,
}


def validate_zone(zone: ReactionZone) -> None:
    """Validate normalized zone coordinates and size."""

    if not zone.label:
        msg = "zone label must not be empty"
        raise ValueError(msg)

    if not 0.0 <= zone.center_x <= 1.0:
        msg = "zone center_x must be in the range [0.0, 1.0]"
        raise ValueError(msg)

    if not 0.0 <= zone.center_y <= 1.0:
        msg = "zone center_y must be in the range [0.0, 1.0]"
        raise ValueError(msg)

    if not 0.0 < zone.scale <= 1.0:
        msg = "zone scale must be in the range (0.0, 1.0]"
        raise ValueError(msg)


def create_default_zones(zone_scale: float) -> list[ReactionZone]:
    """Create four default reaction zones."""

    return [
        ReactionZone("A", center_x=0.28, center_y=0.30, scale=zone_scale),
        ReactionZone("B", center_x=0.72, center_y=0.30, scale=zone_scale),
        ReactionZone("C", center_x=0.28, center_y=0.70, scale=zone_scale),
        ReactionZone("D", center_x=0.72, center_y=0.70, scale=zone_scale),
    ]


def validate_active_zone_index(
    *,
    active_zone_index: int,
    zone_count: int,
) -> None:
    """Validate active zone index."""

    if zone_count <= 0:
        msg = "zone_count must be greater than zero"
        raise ValueError(msg)

    if not 0 <= active_zone_index < zone_count:
        msg = "active_zone_index must point to an existing zone"
        raise ValueError(msg)


def select_next_zone_index(
    rng: random.Random,
    *,
    zone_count: int,
    current_index: int,
) -> int:
    """Select the next active zone index."""

    validate_active_zone_index(
        active_zone_index=current_index,
        zone_count=zone_count,
    )

    if zone_count == 1:
        return current_index

    candidates = [index for index in range(zone_count) if index != current_index]

    return rng.choice(candidates)


def create_initial_game_state(
    *,
    current_time: float,
    active_zone_index: int,
    zone_count: int,
) -> MultiZoneReactionGameState:
    """Create a new game state."""

    validate_active_zone_index(
        active_zone_index=active_zone_index,
        zone_count=zone_count,
    )

    return MultiZoneReactionGameState(
        score=0,
        start_time=current_time,
        last_hit_time=float("-inf"),
        active_zone_index=active_zone_index,
    )


def get_time_left(
    state: MultiZoneReactionGameState,
    config: MultiZoneReactionGameConfig,
    current_time: float,
) -> float:
    """Return remaining game time in seconds."""

    return get_timer_time_left(
        start_time=state.start_time,
        duration_seconds=config.duration_seconds,
        current_time=current_time,
    )


def is_game_finished(
    state: MultiZoneReactionGameState,
    config: MultiZoneReactionGameConfig,
    current_time: float,
) -> bool:
    """Check whether the game timer has finished."""

    return is_timer_finished(
        start_time=state.start_time,
        duration_seconds=config.duration_seconds,
        current_time=current_time,
    )


def is_scoring_proximity(level: ProximityLevel) -> bool:
    """Check whether the current proximity level should award points."""

    return is_scoring_level(level, SCORING_PROXIMITY_LEVELS)


def should_award_points(
    level: ProximityLevel,
    state: MultiZoneReactionGameState,
    config: MultiZoneReactionGameConfig,
    current_time: float,
) -> bool:
    """Check whether points should be awarded for the current frame."""

    return should_award_scoring_points(
        level=level,
        scoring_levels=SCORING_PROXIMITY_LEVELS,
        is_finished=is_game_finished(state, config, current_time),
        last_hit_time=state.last_hit_time,
        cooldown_seconds=config.hit_cooldown_seconds,
        current_time=current_time,
    )


def update_game_state(
    level: ProximityLevel,
    state: MultiZoneReactionGameState,
    config: MultiZoneReactionGameConfig,
    current_time: float,
    next_zone_index: int,
    zone_count: int,
) -> tuple[MultiZoneReactionGameState, bool]:
    """Update game state and return whether points were awarded."""

    validate_active_zone_index(
        active_zone_index=next_zone_index,
        zone_count=zone_count,
    )

    if not should_award_points(level, state, config, current_time):
        return state, False

    updated_state = replace(
        state,
        score=add_points(
            current_score=state.score,
            points=config.points_per_hit,
        ),
        last_hit_time=current_time,
        active_zone_index=next_zone_index,
    )

    return updated_state, True


def get_zone_bounds(
    frame_shape: tuple[int, ...],
    zone: ReactionZone,
) -> tuple[int, int, int, int]:
    """Return zone bounds as x1, y1, x2, y2 pixel coordinates."""

    validate_zone(zone)

    height, width = frame_shape[:2]

    zone_width = max(1, int(width * zone.scale))
    zone_height = max(1, int(height * zone.scale))

    center_x = int(width * zone.center_x)
    center_y = int(height * zone.center_y)

    x1 = max(0, center_x - zone_width // 2)
    y1 = max(0, center_y - zone_height // 2)
    x2 = min(width, x1 + zone_width)
    y2 = min(height, y1 + zone_height)

    x1 = max(0, x2 - zone_width)
    y1 = max(0, y2 - zone_height)

    return x1, y1, x2, y2


def extract_zone_roi(
    frame: NDArray[np.uint8],
    zone: ReactionZone,
) -> NDArray[np.uint8]:
    """Extract a zone region of interest from a frame."""

    x1, y1, x2, y2 = get_zone_bounds(frame.shape, zone)

    return frame[y1:y2, x1:x2]


def draw_zone(
    frame: NDArray[np.uint8],
    zone: ReactionZone,
    *,
    is_active: bool,
    color: tuple[int, int, int],
) -> None:
    """Draw a reaction zone on the frame."""

    x1, y1, x2, y2 = get_zone_bounds(frame.shape, zone)
    thickness = 5 if is_active else 2
    label = f"{zone.label} ACTIVE" if is_active else zone.label

    cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness=thickness)

    cv2.putText(
        frame,
        label,
        (x1 + 10, max(30, y1 - 10)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.75,
        color,
        2,
        cv2.LINE_AA,
    )


def draw_all_zones(
    frame: NDArray[np.uint8],
    zones: list[ReactionZone],
    *,
    active_zone_index: int,
    active_color: tuple[int, int, int],
) -> None:
    """Draw all reaction zones."""

    validate_active_zone_index(
        active_zone_index=active_zone_index,
        zone_count=len(zones),
    )

    inactive_color = (180, 180, 180)

    for index, zone in enumerate(zones):
        is_active = index == active_zone_index
        color = active_color if is_active else inactive_color

        draw_zone(frame, zone, is_active=is_active, color=color)


def draw_alert_border(
    frame: NDArray[np.uint8],
    level: ProximityLevel,
) -> None:
    """Draw a colored alert border around the frame."""

    color = get_alert_color(level)
    thickness = 10 if level is ProximityLevel.VERY_CLOSE else 5

    cv2.rectangle(
        frame,
        (0, 0),
        (frame.shape[1] - 1, frame.shape[0] - 1),
        color,
        thickness=thickness,
    )


def draw_game_panel(
    frame: NDArray[np.uint8],
    *,
    score: int,
    time_left: float,
    active_zone: ReactionZone,
    level: ProximityLevel,
    points_awarded: bool,
) -> None:
    """Draw a simple game panel in the bottom-left corner."""

    panel_x = 20
    panel_y = frame.shape[0] - 140
    panel_width = 480
    panel_height = 115

    cv2.rectangle(
        frame,
        (panel_x, panel_y),
        (panel_x + panel_width, panel_y + panel_height),
        (0, 0, 0),
        thickness=-1,
    )

    cv2.putText(
        frame,
        f"Score: {score}",
        (panel_x + 20, panel_y + 35),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        (0, 255, 255),
        2,
        cv2.LINE_AA,
    )

    cv2.putText(
        frame,
        f"Time: {time_left:04.1f}s",
        (panel_x + 20, panel_y + 70),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )

    cv2.putText(
        frame,
        f"Zone: {active_zone.label}",
        (panel_x + 240, panel_y + 35),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )

    hit_text = "+10 HIT!" if points_awarded else level.value

    cv2.putText(
        frame,
        hit_text,
        (panel_x + 240, panel_y + 70),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        get_alert_color(level),
        2,
        cv2.LINE_AA,
    )


def draw_hud(
    frame: NDArray[np.uint8],
    lines: list[str],
    *,
    origin_x: int = 20,
    origin_y: int = 35,
    line_height: int = 30,
) -> None:
    """Draw a simple colorful HUD on top of the OpenCV frame."""

    for index, text in enumerate(lines):
        y = origin_y + index * line_height

        cv2.putText(
            frame,
            text,
            (origin_x + 2, y + 2),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.75,
            (0, 0, 0),
            3,
            cv2.LINE_AA,
        )

        cv2.putText(
            frame,
            text,
            (origin_x, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.75,
            (0, 255, 255),
            2,
            cv2.LINE_AA,
        )


def run_multi_zone_reaction_game() -> None:
    """Run the interactive multi-zone reaction game demo."""

    print(f"DepthAI: {dai.__version__}")

    config = MultiZoneReactionGameConfig()
    hud_config = HudConfig(title="oak-vision-lab | Multi-Zone Reaction Game")
    rng = random.Random()

    zones = create_default_zones(zone_scale=config.zone_scale)
    show_help = True
    previous_time = time.perf_counter()
    fps = 0.0

    initial_zone_index = rng.randrange(len(zones))
    state = create_initial_game_state(
        current_time=previous_time,
        active_zone_index=initial_zone_index,
        zone_count=len(zones),
    )

    pipeline, max_disparity = create_stereo_disparity_pipeline()

    with dai.Device(pipeline) as device:
        print(f"MXID: {device.getMxId()}")
        print(f"Connected cameras: {device.getConnectedCameras()}")
        print(f"USB speed: {device.getUsbSpeed()}")

        disparity_queue = device.getOutputQueue(
            name="disparity",
            maxSize=4,
            blocking=False,
        )

        while True:
            current_time = time.perf_counter()

            message = disparity_queue.get()
            disparity_frame = message.getFrame()

            active_zone = zones[state.active_zone_index]
            active_roi = extract_zone_roi(disparity_frame, active_zone)
            mean_disparity = compute_mean_disparity(active_roi)
            proximity_level = classify_proximity(
                mean_disparity,
                near_threshold=config.near_threshold,
                very_close_threshold=config.very_close_threshold,
            )

            next_zone_index = select_next_zone_index(
                rng,
                zone_count=len(zones),
                current_index=state.active_zone_index,
            )
            state, points_awarded = update_game_state(
                proximity_level,
                state,
                config,
                current_time,
                next_zone_index=next_zone_index,
                zone_count=len(zones),
            )

            time_left = get_time_left(state, config, current_time)
            is_finished = is_game_finished(state, config, current_time)

            colorized_frame = colorize_disparity_frame(disparity_frame, max_disparity)
            alert_color = get_alert_color(proximity_level)

            draw_all_zones(
                colorized_frame,
                zones,
                active_zone_index=state.active_zone_index,
                active_color=alert_color,
            )
            draw_alert_border(colorized_frame, proximity_level)

            delta_time = current_time - previous_time
            previous_time = current_time

            if delta_time > 0.0:
                fps = 1.0 / delta_time

            active_zone = zones[state.active_zone_index]
            status = (
                f"GAME OVER | final score: {state.score}"
                if is_finished
                else (
                    f"{proximity_level.value} | zone: {active_zone.label} "
                    f"| mean disparity: {mean_disparity:.1f}"
                )
            )

            active_config = HudConfig(
                title=hud_config.title,
                show_fps=True,
                show_help=show_help,
                show_status=True,
            )

            hud_lines = build_hud_lines(
                active_config,
                fps=fps,
                status=status,
            )

            if show_help:
                hud_lines.append("Game: reach the active zone")
                hud_lines.append("Keys: q = quit, h = toggle help, r = restart")

            draw_hud(colorized_frame, hud_lines)
            draw_game_panel(
                colorized_frame,
                score=state.score,
                time_left=time_left,
                active_zone=active_zone,
                level=proximity_level,
                points_awarded=points_awarded,
            )

            cv2.imshow("oak-vision-lab | Multi-Zone Reaction Game", colorized_frame)

            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                break

            if key == ord("h"):
                show_help = not show_help

            if key == ord("r"):
                restart_zone_index = rng.randrange(len(zones))
                state = create_initial_game_state(
                    current_time=time.perf_counter(),
                    active_zone_index=restart_zone_index,
                    zone_count=len(zones),
                )

    cv2.destroyAllWindows()


if __name__ == "__main__":
    run_multi_zone_reaction_game()
