"""OAK-D moving depth target game demo using DepthAI v2 API."""

from __future__ import annotations

import random
import time
from dataclasses import dataclass, replace

import cv2
import depthai as dai
import numpy as np
from numpy.typing import NDArray

from oak_vision_lab.depth.disparity import (
    colorize_disparity_frame,
    compute_mean_disparity,
)
from oak_vision_lab.depth.proximity import (
    ProximityLevel,
    classify_proximity,
    get_alert_color,
)
from oak_vision_lab.visualization.hud import HudConfig, build_hud_lines


@dataclass(frozen=True)
class TargetZone:
    """A target zone described with normalized center coordinates."""

    center_x: float
    center_y: float
    scale: float = 0.22


@dataclass(frozen=True)
class MovingTargetGameConfig:
    """Configuration for the moving target game."""

    duration_seconds: float = 30.0
    hit_cooldown_seconds: float = 0.35
    points_per_hit: int = 10
    near_threshold: float = 25.0
    very_close_threshold: float = 45.0
    target_scale: float = 0.22


@dataclass(frozen=True)
class MovingTargetGameState:
    """Current state of the moving target game."""

    score: int
    start_time: float
    last_hit_time: float
    target: TargetZone


def validate_target(target: TargetZone) -> None:
    """Validate normalized target coordinates and size."""

    if not 0.0 <= target.center_x <= 1.0:
        msg = "target center_x must be in the range [0.0, 1.0]"
        raise ValueError(msg)

    if not 0.0 <= target.center_y <= 1.0:
        msg = "target center_y must be in the range [0.0, 1.0]"
        raise ValueError(msg)

    if not 0.0 < target.scale <= 1.0:
        msg = "target scale must be in the range (0.0, 1.0]"
        raise ValueError(msg)


def generate_random_target(
    rng: random.Random,
    *,
    scale: float,
    min_center: float = 0.2,
    max_center: float = 0.8,
) -> TargetZone:
    """Generate a random target zone inside a normalized safe area."""

    if not 0.0 < min_center < max_center < 1.0:
        msg = "center range must satisfy 0.0 < min_center < max_center < 1.0"
        raise ValueError(msg)

    target = TargetZone(
        center_x=rng.uniform(min_center, max_center),
        center_y=rng.uniform(min_center, max_center),
        scale=scale,
    )
    validate_target(target)

    return target


def create_initial_game_state(
    current_time: float,
    target: TargetZone,
) -> MovingTargetGameState:
    """Create a new game state."""

    validate_target(target)

    return MovingTargetGameState(
        score=0,
        start_time=current_time,
        last_hit_time=float("-inf"),
        target=target,
    )


def get_time_left(
    state: MovingTargetGameState,
    config: MovingTargetGameConfig,
    current_time: float,
) -> float:
    """Return remaining game time in seconds."""

    elapsed_time = current_time - state.start_time

    return max(0.0, config.duration_seconds - elapsed_time)


def is_game_finished(
    state: MovingTargetGameState,
    config: MovingTargetGameConfig,
    current_time: float,
) -> bool:
    """Check whether the game timer has finished."""

    return get_time_left(state, config, current_time) <= 0.0


def is_scoring_proximity(level: ProximityLevel) -> bool:
    """Check whether the current proximity level should award points."""

    return level in {ProximityLevel.NEAR, ProximityLevel.VERY_CLOSE}


def should_award_points(
    level: ProximityLevel,
    state: MovingTargetGameState,
    config: MovingTargetGameConfig,
    current_time: float,
) -> bool:
    """Check whether points should be awarded for the current frame."""

    if is_game_finished(state, config, current_time):
        return False

    if not is_scoring_proximity(level):
        return False

    time_since_last_hit = current_time - state.last_hit_time

    return time_since_last_hit >= config.hit_cooldown_seconds


def update_game_state(
    level: ProximityLevel,
    state: MovingTargetGameState,
    config: MovingTargetGameConfig,
    current_time: float,
    next_target: TargetZone,
) -> tuple[MovingTargetGameState, bool]:
    """Update game state and return whether points were awarded."""

    validate_target(next_target)

    if not should_award_points(level, state, config, current_time):
        return state, False

    updated_state = replace(
        state,
        score=state.score + config.points_per_hit,
        last_hit_time=current_time,
        target=next_target,
    )

    return updated_state, True


def get_camera_socket(name: str, fallback_name: str) -> dai.CameraBoardSocket:
    """Get a camera socket while supporting older and newer DepthAI naming styles."""

    if hasattr(dai.CameraBoardSocket, name):
        return getattr(dai.CameraBoardSocket, name)

    return getattr(dai.CameraBoardSocket, fallback_name)


def create_depth_pipeline() -> tuple[dai.Pipeline, float]:
    """Create a DepthAI v2 stereo disparity pipeline."""

    pipeline = dai.Pipeline()

    left_camera = pipeline.create(dai.node.MonoCamera)
    right_camera = pipeline.create(dai.node.MonoCamera)
    stereo = pipeline.create(dai.node.StereoDepth)
    output = pipeline.create(dai.node.XLinkOut)

    output.setStreamName("disparity")

    left_camera.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)
    right_camera.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)

    left_camera.setBoardSocket(get_camera_socket("LEFT", "CAM_B"))
    right_camera.setBoardSocket(get_camera_socket("RIGHT", "CAM_C"))

    stereo.setDefaultProfilePreset(dai.node.StereoDepth.PresetMode.HIGH_DENSITY)
    stereo.setLeftRightCheck(True)
    stereo.setExtendedDisparity(False)
    stereo.setSubpixel(False)

    left_camera.out.link(stereo.left)
    right_camera.out.link(stereo.right)
    stereo.disparity.link(output.input)

    max_disparity = stereo.initialConfig.getMaxDisparity()

    return pipeline, max_disparity


def get_target_bounds(
    frame_shape: tuple[int, ...],
    target: TargetZone,
) -> tuple[int, int, int, int]:
    """Return target bounds as x1, y1, x2, y2 pixel coordinates."""

    validate_target(target)

    height, width = frame_shape[:2]

    target_width = max(1, int(width * target.scale))
    target_height = max(1, int(height * target.scale))

    center_x = int(width * target.center_x)
    center_y = int(height * target.center_y)

    x1 = max(0, center_x - target_width // 2)
    y1 = max(0, center_y - target_height // 2)
    x2 = min(width, x1 + target_width)
    y2 = min(height, y1 + target_height)

    x1 = max(0, x2 - target_width)
    y1 = max(0, y2 - target_height)

    return x1, y1, x2, y2


def extract_target_roi(
    frame: NDArray[np.uint8],
    target: TargetZone,
) -> NDArray[np.uint8]:
    """Extract the target region of interest from a frame."""

    x1, y1, x2, y2 = get_target_bounds(frame.shape, target)

    return frame[y1:y2, x1:x2]


def draw_target_zone(
    frame: NDArray[np.uint8],
    target: TargetZone,
    color: tuple[int, int, int],
) -> None:
    """Draw the current target zone on the frame."""

    x1, y1, x2, y2 = get_target_bounds(frame.shape, target)

    cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness=4)

    cv2.putText(
        frame,
        "TARGET",
        (x1 + 10, max(30, y1 - 10)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        color,
        2,
        cv2.LINE_AA,
    )


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
    level: ProximityLevel,
    points_awarded: bool,
) -> None:
    """Draw a simple game panel in the bottom-left corner."""

    panel_x = 20
    panel_y = frame.shape[0] - 130
    panel_width = 430
    panel_height = 105

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

    hit_text = "+10 HIT!" if points_awarded else level.value

    cv2.putText(
        frame,
        hit_text,
        (panel_x + 220, panel_y + 70),
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


def run_moving_depth_target_game() -> None:
    """Run the interactive moving depth target game demo."""

    print(f"DepthAI: {dai.__version__}")

    config = MovingTargetGameConfig()
    hud_config = HudConfig(title="oak-vision-lab | Moving Depth Target Game")
    rng = random.Random()

    show_help = True
    previous_time = time.perf_counter()
    fps = 0.0

    initial_target = generate_random_target(rng, scale=config.target_scale)
    state = create_initial_game_state(previous_time, target=initial_target)

    pipeline, max_disparity = create_depth_pipeline()

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

            target_roi = extract_target_roi(disparity_frame, state.target)
            mean_disparity = compute_mean_disparity(target_roi)
            proximity_level = classify_proximity(
                mean_disparity,
                near_threshold=config.near_threshold,
                very_close_threshold=config.very_close_threshold,
            )

            next_target = generate_random_target(rng, scale=config.target_scale)
            state, points_awarded = update_game_state(
                proximity_level,
                state,
                config,
                current_time,
                next_target=next_target,
            )

            time_left = get_time_left(state, config, current_time)
            is_finished = is_game_finished(state, config, current_time)

            colorized_frame = colorize_disparity_frame(disparity_frame, max_disparity)
            alert_color = get_alert_color(proximity_level)

            draw_target_zone(colorized_frame, state.target, color=alert_color)
            draw_alert_border(colorized_frame, proximity_level)

            delta_time = current_time - previous_time
            previous_time = current_time

            if delta_time > 0.0:
                fps = 1.0 / delta_time

            status = (
                f"GAME OVER | final score: {state.score}"
                if is_finished
                else f"{proximity_level.value} | mean disparity: {mean_disparity:.1f}"
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
                hud_lines.append("Game: move hand/object into the target zone")
                hud_lines.append("Keys: q = quit, h = toggle help, r = restart")

            draw_hud(colorized_frame, hud_lines)
            draw_game_panel(
                colorized_frame,
                score=state.score,
                time_left=time_left,
                level=proximity_level,
                points_awarded=points_awarded,
            )

            cv2.imshow("oak-vision-lab | Moving Depth Target Game", colorized_frame)

            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                break

            if key == ord("h"):
                show_help = not show_help

            if key == ord("r"):
                restart_target = generate_random_target(
                    rng,
                    scale=config.target_scale,
                )
                state = create_initial_game_state(
                    time.perf_counter(),
                    target=restart_target,
                )

    cv2.destroyAllWindows()


if __name__ == "__main__":
    run_moving_depth_target_game()
