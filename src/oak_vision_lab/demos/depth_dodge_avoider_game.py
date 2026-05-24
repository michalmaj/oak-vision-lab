"""Depth dodge / avoider game demo based on RGB preview and stereo disparity."""

from __future__ import annotations

import random
import time
from dataclasses import dataclass

import cv2
import depthai as dai
import numpy as np

from oak_vision_lab.depth.disparity import colorize_disparity_frame
from oak_vision_lab.depth.proximity import ProximityLevel, classify_proximity

WINDOW_NAME = "oak-vision-lab | Depth Dodge / Avoider Game"

RGB_STREAM_NAME = "rgb"
DISPARITY_STREAM_NAME = "disparity"

DEFAULT_ZONE_COUNT = 4
DEFAULT_LIVES = 3
DEFAULT_ZONE_CHANGE_SECONDS = 1.4
DEFAULT_COLLISION_COOLDOWN_SECONDS = 0.8

DEFAULT_NEAR_THRESHOLD = 25.0
DEFAULT_VERY_CLOSE_THRESHOLD = 45.0

RGB_PREVIEW_WIDTH = 640
RGB_PREVIEW_HEIGHT = 400


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


def create_rgb_disparity_pipeline() -> tuple[dai.Pipeline, float]:
    """Create an OAK-D pipeline with RGB preview and stereo disparity output."""

    pipeline = dai.Pipeline()

    color_camera = pipeline.create(dai.node.ColorCamera)
    mono_left = pipeline.create(dai.node.MonoCamera)
    mono_right = pipeline.create(dai.node.MonoCamera)
    stereo = pipeline.create(dai.node.StereoDepth)

    rgb_output = pipeline.create(dai.node.XLinkOut)
    disparity_output = pipeline.create(dai.node.XLinkOut)

    rgb_output.setStreamName(RGB_STREAM_NAME)
    disparity_output.setStreamName(DISPARITY_STREAM_NAME)

    color_camera.setBoardSocket(dai.CameraBoardSocket.RGB)
    color_camera.setPreviewSize(RGB_PREVIEW_WIDTH, RGB_PREVIEW_HEIGHT)
    color_camera.setInterleaved(False)
    color_camera.setColorOrder(dai.ColorCameraProperties.ColorOrder.BGR)

    mono_left.setBoardSocket(dai.CameraBoardSocket.LEFT)
    mono_right.setBoardSocket(dai.CameraBoardSocket.RIGHT)
    mono_left.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)
    mono_right.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)

    stereo.setDefaultProfilePreset(dai.node.StereoDepth.PresetMode.HIGH_DENSITY)
    stereo.setLeftRightCheck(True)
    stereo.setSubpixel(False)

    mono_left.out.link(stereo.left)
    mono_right.out.link(stereo.right)

    color_camera.preview.link(rgb_output.input)
    stereo.disparity.link(disparity_output.input)

    max_disparity = float(stereo.initialConfig.getMaxDisparity())

    return pipeline, max_disparity


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


def measure_dodge_zones(
    *,
    disparity_frame: np.ndarray,
    zones: list[DodgeZone],
) -> list[ZoneMeasurement]:
    """Measure all dodge zones in a disparity frame."""

    measurements: list[ZoneMeasurement] = []

    for zone in zones:
        mean_disparity = compute_zone_mean_disparity(
            disparity_frame,
            zone,
        )
        proximity_level = classify_proximity(
            mean_disparity=mean_disparity,
            near_threshold=DEFAULT_NEAR_THRESHOLD,
            very_close_threshold=DEFAULT_VERY_CLOSE_THRESHOLD,
        )

        measurements.append(
            ZoneMeasurement(
                zone=zone,
                mean_disparity=mean_disparity,
                proximity_level=proximity_level,
                occupied=is_zone_occupied(proximity_level),
            ),
        )

    return measurements


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


def scale_dodge_zone(
    *,
    zone: DodgeZone,
    source_width: int,
    source_height: int,
    target_width: int,
    target_height: int,
) -> DodgeZone:
    """Scale a dodge zone from one frame size to another."""

    if source_width <= 0 or source_height <= 0:
        msg = "source dimensions must be positive"
        raise ValueError(msg)

    if target_width <= 0 or target_height <= 0:
        msg = "target dimensions must be positive"
        raise ValueError(msg)

    scale_x = target_width / source_width
    scale_y = target_height / source_height

    return DodgeZone(
        index=zone.index,
        label=zone.label,
        x=round(zone.x * scale_x),
        y=round(zone.y * scale_y),
        width=round(zone.width * scale_x),
        height=round(zone.height * scale_y),
    )


def scale_dodge_zones(
    *,
    zones: list[DodgeZone],
    source_width: int,
    source_height: int,
    target_width: int,
    target_height: int,
) -> list[DodgeZone]:
    """Scale dodge zones from one frame size to another."""

    return [
        scale_dodge_zone(
            zone=zone,
            source_width=source_width,
            source_height=source_height,
            target_width=target_width,
            target_height=target_height,
        )
        for zone in zones
    ]


def get_zone_color(
    *,
    zone_index: int,
    active_zone_index: int,
    measurement: ZoneMeasurement,
) -> tuple[int, int, int]:
    """Return BGR color for a dodge zone."""

    if zone_index == active_zone_index and measurement.occupied:
        return (0, 0, 255)

    if zone_index == active_zone_index:
        return (0, 180, 255)

    if measurement.occupied:
        return (0, 200, 0)

    return (110, 110, 110)


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


def draw_dodge_zone(
    frame: np.ndarray,
    *,
    measurement: ZoneMeasurement,
    active_zone_index: int,
) -> None:
    """Draw a single dodge zone."""

    zone = measurement.zone
    color = get_zone_color(
        zone_index=zone.index,
        active_zone_index=active_zone_index,
        measurement=measurement,
    )

    overlay = frame.copy()

    if zone.index == active_zone_index:
        fill_alpha = 0.42
    elif measurement.occupied:
        fill_alpha = 0.24
    else:
        fill_alpha = 0.08

    cv2.rectangle(
        overlay,
        (zone.x, zone.y),
        (zone.x2, zone.y2),
        color,
        -1,
    )
    cv2.addWeighted(
        overlay,
        fill_alpha,
        frame,
        1.0 - fill_alpha,
        0,
        frame,
    )

    thickness = 4 if zone.index == active_zone_index else 2

    cv2.rectangle(
        frame,
        (zone.x, zone.y),
        (zone.x2, zone.y2),
        color,
        thickness,
    )

    if zone.index == active_zone_index:
        label = "DANGER"
    elif measurement.occupied:
        label = "PLAYER"
    else:
        label = zone.label

    draw_text(
        frame,
        label,
        (zone.x + 12, zone.y + 34),
        scale=0.68,
        color=color,
        thickness=2,
    )
    draw_text(
        frame,
        f"{measurement.mean_disparity:.1f}",
        (zone.x + 12, zone.y + 62),
        scale=0.5,
        color=(255, 255, 255),
        thickness=1,
    )


def draw_dodge_zones(
    frame: np.ndarray,
    *,
    measurements: list[ZoneMeasurement],
    active_zone_index: int,
) -> None:
    """Draw all dodge zones."""

    for measurement in measurements:
        draw_dodge_zone(
            frame,
            measurement=measurement,
            active_zone_index=active_zone_index,
        )


def draw_rgb_hud(
    frame: np.ndarray,
    *,
    update_result: DodgeUpdateResult,
    time_to_next_zone: float,
) -> None:
    """Draw user-facing game HUD on the RGB frame."""

    state = update_result.state
    message = get_dodge_message(
        collision=update_result.collision,
        score_awarded=update_result.score_awarded,
        state=state,
    )

    lines = [
        "Depth Dodge / Avoider Game",
        "Avoid the highlighted danger zone",
        f"Score: {state.score}",
        f"Lives: {state.lives}",
        f"Collisions: {state.collisions}",
        f"Active zone: {state.active_zone_index + 1}",
        f"Next zone: {max(0.0, time_to_next_zone):.1f}s",
        message,
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


def draw_disparity_hud(frame: np.ndarray, *, max_disparity: float) -> None:
    """Draw measurement/debug information on the disparity frame."""

    lines = [
        "Disparity danger zones",
        f"Zones: {DEFAULT_ZONE_COUNT}",
        f"Max disparity: {max_disparity:.1f}",
        "Red/orange zone must stay empty",
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


def create_split_screen(
    *,
    rgb_frame: np.ndarray,
    disparity_frame: np.ndarray,
) -> np.ndarray:
    """Create a side-by-side RGB and disparity presentation frame."""

    if rgb_frame.shape[:2] != disparity_frame.shape[:2]:
        disparity_frame = cv2.resize(
            disparity_frame,
            (rgb_frame.shape[1], rgb_frame.shape[0]),
            interpolation=cv2.INTER_NEAREST,
        )

    return np.hstack((rgb_frame, disparity_frame))


def run() -> None:
    """Run the OAK-D depth dodge / avoider game demo."""

    pipeline, max_disparity = create_rgb_disparity_pipeline()
    rng = random.Random()

    with dai.Device(pipeline) as device:
        rgb_queue = device.getOutputQueue(
            name=RGB_STREAM_NAME,
            maxSize=4,
            blocking=False,
        )
        disparity_queue = device.getOutputQueue(
            name=DISPARITY_STREAM_NAME,
            maxSize=4,
            blocking=False,
        )

        cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)

        current_time = time.monotonic()
        state = create_initial_state(current_time=current_time, rng=rng)
        last_update_result = DodgeUpdateResult(
            state=state,
            collision=False,
            zone_changed=False,
            score_awarded=False,
        )

        while True:
            rgb_message = rgb_queue.get()
            disparity_message = disparity_queue.get()

            rgb_frame = rgb_message.getCvFrame()
            disparity_frame = disparity_message.getFrame()

            disparity_height, disparity_width = disparity_frame.shape[:2]
            rgb_height, rgb_width = rgb_frame.shape[:2]

            disparity_zones = create_dodge_zones(
                frame_width=disparity_width,
                frame_height=disparity_height,
            )
            measurements = measure_dodge_zones(
                disparity_frame=disparity_frame,
                zones=disparity_zones,
            )

            current_time = time.monotonic()
            update_result = update_dodge_game(
                state=state,
                measurements=measurements,
                current_time=current_time,
                rng=rng,
            )
            state = update_result.state
            last_update_result = update_result

            rgb_zones = scale_dodge_zones(
                zones=disparity_zones,
                source_width=disparity_width,
                source_height=disparity_height,
                target_width=rgb_width,
                target_height=rgb_height,
            )
            rgb_measurements = [
                ZoneMeasurement(
                    zone=rgb_zone,
                    mean_disparity=measurement.mean_disparity,
                    proximity_level=measurement.proximity_level,
                    occupied=measurement.occupied,
                )
                for rgb_zone, measurement in zip(
                    rgb_zones,
                    measurements,
                    strict=True,
                )
            ]

            colorized_disparity = colorize_disparity_frame(
                disparity_frame,
                max_disparity=max_disparity,
            )

            draw_dodge_zones(
                rgb_frame,
                measurements=rgb_measurements,
                active_zone_index=state.active_zone_index,
            )
            draw_dodge_zones(
                colorized_disparity,
                measurements=measurements,
                active_zone_index=state.active_zone_index,
            )

            time_to_next_zone = state.next_zone_change_time - current_time

            draw_rgb_hud(
                rgb_frame,
                update_result=last_update_result,
                time_to_next_zone=time_to_next_zone,
            )
            draw_disparity_hud(
                colorized_disparity,
                max_disparity=max_disparity,
            )

            split_screen = create_split_screen(
                rgb_frame=rgb_frame,
                disparity_frame=colorized_disparity,
            )

            cv2.imshow(WINDOW_NAME, split_screen)

            key = cv2.waitKey(1) & 0xFF

            if key in {ord("q"), 27}:
                break

            if key == ord("r"):
                current_time = time.monotonic()
                state = create_initial_state(current_time=current_time, rng=rng)
                last_update_result = DodgeUpdateResult(
                    state=state,
                    collision=False,
                    zone_changed=False,
                    score_awarded=False,
                )

    cv2.destroyWindow(WINDOW_NAME)


if __name__ == "__main__":
    run()
