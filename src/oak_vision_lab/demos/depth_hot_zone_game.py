"""OAK-D depth hot zone game demo using DepthAI v2 API."""

from __future__ import annotations

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
class HotZoneGameConfig:
    """Configuration for the hot zone game logic."""

    duration_seconds: float = 30.0
    hit_cooldown_seconds: float = 0.35
    points_per_hit: int = 10
    roi_scale: float = 0.25
    near_threshold: float = 25.0
    very_close_threshold: float = 45.0


@dataclass(frozen=True)
class HotZoneGameState:
    """Current state of the hot zone game."""

    score: int
    start_time: float
    last_hit_time: float


def create_initial_game_state(current_time: float) -> HotZoneGameState:
    """Create a new game state."""

    return HotZoneGameState(
        score=0,
        start_time=current_time,
        last_hit_time=float("-inf"),
    )


def get_time_left(
    state: HotZoneGameState,
    config: HotZoneGameConfig,
    current_time: float,
) -> float:
    """Return remaining game time in seconds."""

    elapsed_time = current_time - state.start_time

    return max(0.0, config.duration_seconds - elapsed_time)


def is_game_finished(
    state: HotZoneGameState,
    config: HotZoneGameConfig,
    current_time: float,
) -> bool:
    """Check whether the game timer has finished."""

    return get_time_left(state, config, current_time) <= 0.0


def is_scoring_proximity(level: ProximityLevel) -> bool:
    """Check whether the current proximity level should award points."""

    return level in {ProximityLevel.NEAR, ProximityLevel.VERY_CLOSE}


def should_award_points(
    level: ProximityLevel,
    state: HotZoneGameState,
    config: HotZoneGameConfig,
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
    state: HotZoneGameState,
    config: HotZoneGameConfig,
    current_time: float,
) -> tuple[HotZoneGameState, bool]:
    """Update game state and return whether points were awarded."""

    if not should_award_points(level, state, config, current_time):
        return state, False

    updated_state = replace(
        state,
        score=state.score + config.points_per_hit,
        last_hit_time=current_time,
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


def extract_center_roi(
    frame: NDArray[np.uint8],
    roi_scale: float,
) -> NDArray[np.uint8]:
    """Extract a centered region of interest from a frame."""

    if not 0.0 < roi_scale <= 1.0:
        msg = "roi_scale must be in the range (0.0, 1.0]"
        raise ValueError(msg)

    height, width = frame.shape[:2]

    roi_width = max(1, int(width * roi_scale))
    roi_height = max(1, int(height * roi_scale))

    x1 = (width - roi_width) // 2
    y1 = (height - roi_height) // 2
    x2 = x1 + roi_width
    y2 = y1 + roi_height

    return frame[y1:y2, x1:x2]


def draw_center_roi(
    frame: NDArray[np.uint8],
    roi_scale: float,
    color: tuple[int, int, int],
) -> None:
    """Draw the centered hot zone on the frame."""

    height, width = frame.shape[:2]

    roi_width = max(1, int(width * roi_scale))
    roi_height = max(1, int(height * roi_scale))

    x1 = (width - roi_width) // 2
    y1 = (height - roi_height) // 2
    x2 = x1 + roi_width
    y2 = y1 + roi_height

    cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness=3)


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
    panel_width = 380
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
        (panel_x + 200, panel_y + 70),
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


def run_depth_hot_zone_game() -> None:
    """Run the interactive depth hot zone game demo."""

    print(f"DepthAI: {dai.__version__}")

    config = HotZoneGameConfig()
    hud_config = HudConfig(title="oak-vision-lab | Depth Hot Zone Game")

    show_help = True
    previous_time = time.perf_counter()
    fps = 0.0
    state = create_initial_game_state(previous_time)

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

            center_roi = extract_center_roi(disparity_frame, roi_scale=config.roi_scale)
            mean_disparity = compute_mean_disparity(center_roi)
            proximity_level = classify_proximity(
                mean_disparity,
                near_threshold=config.near_threshold,
                very_close_threshold=config.very_close_threshold,
            )

            state, points_awarded = update_game_state(
                proximity_level,
                state,
                config,
                current_time,
            )

            time_left = get_time_left(state, config, current_time)
            is_finished = is_game_finished(state, config, current_time)

            colorized_frame = colorize_disparity_frame(disparity_frame, max_disparity)
            alert_color = get_alert_color(proximity_level)

            draw_center_roi(
                colorized_frame, roi_scale=config.roi_scale, color=alert_color
            )
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
                hud_lines.append("Game: move hand/object into the hot zone")
                hud_lines.append("Keys: q = quit, h = toggle help, r = restart")

            draw_hud(colorized_frame, hud_lines)
            draw_game_panel(
                colorized_frame,
                score=state.score,
                time_left=time_left,
                level=proximity_level,
                points_awarded=points_awarded,
            )

            cv2.imshow("oak-vision-lab | Depth Hot Zone Game", colorized_frame)

            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                break

            if key == ord("h"):
                show_help = not show_help

            if key == ord("r"):
                state = create_initial_game_state(time.perf_counter())

    cv2.destroyAllWindows()


if __name__ == "__main__":
    run_depth_hot_zone_game()
