"""Object distance meter demo based on RGB preview and stereo disparity."""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import depthai as dai
import numpy as np

from oak_vision_lab.depth.disparity import colorize_disparity_frame
from oak_vision_lab.depth.proximity import ProximityLevel, classify_proximity

WINDOW_NAME = "oak-vision-lab | Object Distance Meter"

RGB_STREAM_NAME = "rgb"
DISPARITY_STREAM_NAME = "disparity"

DEFAULT_NEAR_THRESHOLD = 25.0
DEFAULT_VERY_CLOSE_THRESHOLD = 45.0

METER_REGION_WIDTH_RATIO = 0.34
METER_REGION_HEIGHT_RATIO = 0.34

DEFAULT_METER_SEGMENTS = 20

RGB_PREVIEW_WIDTH = 640
RGB_PREVIEW_HEIGHT = 400


@dataclass(frozen=True)
class MeterRegion:
    """Rectangular measurement region in image coordinates."""

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
class MeterSegments:
    """Text-friendly representation of a proximity meter."""

    filled: int
    empty: int

    @property
    def total(self) -> int:
        """Return the total number of meter segments."""

        return self.filled + self.empty


@dataclass(frozen=True)
class DistanceMeterStats:
    """Aggregated distance meter statistics."""

    sample_count: int = 0
    min_disparity: float | None = None
    max_disparity: float | None = None
    peak_level: ProximityLevel = ProximityLevel.SAFE


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


def get_center_meter_region(
    *,
    frame_width: int,
    frame_height: int,
    width_ratio: float = METER_REGION_WIDTH_RATIO,
    height_ratio: float = METER_REGION_HEIGHT_RATIO,
) -> MeterRegion:
    """Return a centered measurement region for the given frame size."""

    width = int(frame_width * width_ratio)
    height = int(frame_height * height_ratio)
    x = (frame_width - width) // 2
    y = (frame_height - height) // 2

    return MeterRegion(x=x, y=y, width=width, height=height)


def compute_region_mean_disparity(
    disparity_frame: np.ndarray,
    region: MeterRegion,
) -> float:
    """Compute mean non-zero disparity inside the measurement region."""

    roi = disparity_frame[region.y : region.y2, region.x : region.x2]

    if roi.size == 0:
        return 0.0

    valid_pixels = roi[roi > 0]

    if valid_pixels.size == 0:
        return 0.0

    return float(np.mean(valid_pixels))


def normalize_disparity_value(
    *,
    mean_disparity: float,
    max_disparity: float,
) -> float:
    """Normalize disparity to a 0.0-1.0 range."""

    if max_disparity <= 0.0:
        return 0.0

    normalized = mean_disparity / max_disparity

    return max(0.0, min(1.0, normalized))


def create_meter_segments(
    *,
    normalized_value: float,
    segment_count: int = DEFAULT_METER_SEGMENTS,
) -> MeterSegments:
    """Create filled and empty segment counts for a proximity meter."""

    if segment_count <= 0:
        msg = "segment_count must be positive"
        raise ValueError(msg)

    clamped_value = max(0.0, min(1.0, normalized_value))
    filled = round(clamped_value * segment_count)
    empty = segment_count - filled

    return MeterSegments(filled=filled, empty=empty)


def get_proximity_message(proximity_level: ProximityLevel) -> str:
    """Return a short HUD message for the current proximity level."""

    messages = {
        ProximityLevel.SAFE: "Object is keeping a respectful distance.",
        ProximityLevel.NEAR: "Object entered the measurement zone.",
        ProximityLevel.VERY_CLOSE: "Object is very close to the camera.",
    }

    return messages[proximity_level]


def get_proximity_level_rank(proximity_level: ProximityLevel) -> int:
    """Return numeric rank for comparing proximity levels."""

    ranks = {
        ProximityLevel.SAFE: 0,
        ProximityLevel.NEAR: 1,
        ProximityLevel.VERY_CLOSE: 2,
    }

    return ranks[proximity_level]


def update_distance_stats(
    *,
    stats: DistanceMeterStats,
    mean_disparity: float,
    proximity_level: ProximityLevel,
) -> DistanceMeterStats:
    """Return updated distance meter statistics."""

    if stats.min_disparity is None:
        min_disparity = mean_disparity
    else:
        min_disparity = min(stats.min_disparity, mean_disparity)

    if stats.max_disparity is None:
        max_disparity = mean_disparity
    else:
        max_disparity = max(stats.max_disparity, mean_disparity)

    if get_proximity_level_rank(proximity_level) > get_proximity_level_rank(
        stats.peak_level,
    ):
        peak_level = proximity_level
    else:
        peak_level = stats.peak_level

    return DistanceMeterStats(
        sample_count=stats.sample_count + 1,
        min_disparity=min_disparity,
        max_disparity=max_disparity,
        peak_level=peak_level,
    )


def get_proximity_color(proximity_level: ProximityLevel) -> tuple[int, int, int]:
    """Return BGR color for a proximity level."""

    colors = {
        ProximityLevel.SAFE: (0, 200, 0),
        ProximityLevel.NEAR: (0, 180, 255),
        ProximityLevel.VERY_CLOSE: (0, 0, 255),
    }

    return colors[proximity_level]


def format_optional_disparity(value: float | None) -> str:
    """Format optional disparity value for HUD text."""

    if value is None:
        return "--"

    return f"{value:.1f}"


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


def draw_meter_region(
    frame: np.ndarray,
    region: MeterRegion,
    *,
    proximity_level: ProximityLevel,
    label: str,
) -> None:
    """Draw the measurement region on a frame."""

    color = get_proximity_color(proximity_level)

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
        scale=0.75,
        color=color,
        thickness=2,
    )


def draw_proximity_bar(
    frame: np.ndarray,
    *,
    segments: MeterSegments,
    origin: tuple[int, int],
    segment_width: int = 18,
    segment_height: int = 24,
    gap: int = 4,
    color: tuple[int, int, int],
) -> None:
    """Draw a segmented proximity bar."""

    x, y = origin

    for index in range(segments.total):
        x1 = x + index * (segment_width + gap)
        y1 = y
        x2 = x1 + segment_width
        y2 = y1 + segment_height

        if index < segments.filled:
            thickness = -1
            rectangle_color = color
        else:
            thickness = 2
            rectangle_color = (120, 120, 120)

        cv2.rectangle(
            frame,
            (x1, y1),
            (x2, y2),
            rectangle_color,
            thickness,
        )


def draw_rgb_hud(
    frame: np.ndarray,
    *,
    mean_disparity: float,
    max_disparity: float,
    proximity_level: ProximityLevel,
    stats: DistanceMeterStats,
) -> None:
    """Draw the user-facing HUD on the RGB frame."""

    normalized_value = normalize_disparity_value(
        mean_disparity=mean_disparity,
        max_disparity=max_disparity,
    )
    segments = create_meter_segments(normalized_value=normalized_value)
    color = get_proximity_color(proximity_level)

    lines = [
        "Object Distance Meter",
        f"Mean disparity: {mean_disparity:.1f}",
        f"Proximity: {proximity_level.value}",
        f"Samples: {stats.sample_count}",
        f"Min / Max: {format_optional_disparity(stats.min_disparity)} / "
        f"{format_optional_disparity(stats.max_disparity)}",
        f"Peak level: {stats.peak_level.value}",
        get_proximity_message(proximity_level),
        "R - reset stats | Q / ESC - quit",
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

    draw_text(
        frame,
        "Proximity meter",
        (20, frame.shape[0] - 54),
        scale=0.62,
        color=(255, 255, 255),
        thickness=1,
    )
    draw_proximity_bar(
        frame,
        segments=segments,
        origin=(20, frame.shape[0] - 34),
        color=color,
    )


def draw_disparity_hud(
    frame: np.ndarray,
    *,
    mean_disparity: float,
    max_disparity: float,
) -> None:
    """Draw measurement details on the disparity frame."""

    normalized_value = normalize_disparity_value(
        mean_disparity=mean_disparity,
        max_disparity=max_disparity,
    )

    lines = [
        "Disparity measurement view",
        f"Max disparity: {max_disparity:.1f}",
        f"Normalized: {normalized_value:.2f}",
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
    """Run the OAK-D object distance meter demo."""

    pipeline, max_disparity = create_rgb_disparity_pipeline()

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

        stats = DistanceMeterStats()

        while True:
            rgb_message = rgb_queue.get()
            disparity_message = disparity_queue.get()

            rgb_frame = rgb_message.getCvFrame()
            disparity_frame = disparity_message.getFrame()

            disparity_height, disparity_width = disparity_frame.shape[:2]
            rgb_height, rgb_width = rgb_frame.shape[:2]

            disparity_region = get_center_meter_region(
                frame_width=disparity_width,
                frame_height=disparity_height,
            )
            rgb_region = get_center_meter_region(
                frame_width=rgb_width,
                frame_height=rgb_height,
            )

            mean_disparity = compute_region_mean_disparity(
                disparity_frame,
                disparity_region,
            )
            proximity_level = classify_proximity(
                mean_disparity=mean_disparity,
                near_threshold=DEFAULT_NEAR_THRESHOLD,
                very_close_threshold=DEFAULT_VERY_CLOSE_THRESHOLD,
            )

            stats = update_distance_stats(
                stats=stats,
                mean_disparity=mean_disparity,
                proximity_level=proximity_level,
            )

            colorized_disparity = colorize_disparity_frame(
                disparity_frame,
                max_disparity=max_disparity,
            )

            draw_meter_region(
                rgb_frame,
                rgb_region,
                proximity_level=proximity_level,
                label="RGB HUD ROI",
            )
            draw_meter_region(
                colorized_disparity,
                disparity_region,
                proximity_level=proximity_level,
                label="MEASURE ROI",
            )
            draw_rgb_hud(
                rgb_frame,
                mean_disparity=mean_disparity,
                max_disparity=max_disparity,
                proximity_level=proximity_level,
                stats=stats,
            )
            draw_disparity_hud(
                colorized_disparity,
                mean_disparity=mean_disparity,
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
                stats = DistanceMeterStats()

    cv2.destroyWindow(WINDOW_NAME)


if __name__ == "__main__":
    run()
