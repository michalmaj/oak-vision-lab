"""Closest object tracker demo based on RGB preview and stereo disparity."""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import depthai as dai
import numpy as np

from oak_vision_lab.depth.disparity import colorize_disparity_frame
from oak_vision_lab.depth.proximity import ProximityLevel, classify_proximity

WINDOW_NAME = "oak-vision-lab | Closest Object Tracker"

RGB_STREAM_NAME = "rgb"
DISPARITY_STREAM_NAME = "disparity"

DEFAULT_GRID_ROWS = 3
DEFAULT_GRID_COLUMNS = 4
DEFAULT_MIN_MEAN_DISPARITY = 5.0

DEFAULT_NEAR_THRESHOLD = 25.0
DEFAULT_VERY_CLOSE_THRESHOLD = 45.0

RGB_PREVIEW_WIDTH = 640
RGB_PREVIEW_HEIGHT = 400


@dataclass(frozen=True)
class TrackingRegion:
    """Rectangular tracking region in image coordinates."""

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
class RegionScore:
    """Mean disparity score for a tracking region."""

    region: TrackingRegion
    mean_disparity: float


@dataclass(frozen=True)
class ClosestObjectResult:
    """Closest object tracking result."""

    region: TrackingRegion | None
    mean_disparity: float
    detected: bool


@dataclass(frozen=True)
class TrackerStats:
    """Aggregated closest object tracker statistics."""

    frame_count: int = 0
    detection_count: int = 0
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


def create_tracking_grid(
    *,
    frame_width: int,
    frame_height: int,
    rows: int = DEFAULT_GRID_ROWS,
    columns: int = DEFAULT_GRID_COLUMNS,
) -> list[TrackingRegion]:
    """Create a regular grid of tracking regions."""

    if frame_width <= 0 or frame_height <= 0:
        msg = "frame dimensions must be positive"
        raise ValueError(msg)

    if rows <= 0 or columns <= 0:
        msg = "rows and columns must be positive"
        raise ValueError(msg)

    cell_width = frame_width // columns
    cell_height = frame_height // rows

    regions: list[TrackingRegion] = []

    for row in range(rows):
        for column in range(columns):
            x = column * cell_width
            y = row * cell_height

            width = frame_width - x if column == columns - 1 else cell_width

            height = frame_height - y if row == rows - 1 else cell_height

            regions.append(
                TrackingRegion(
                    x=x,
                    y=y,
                    width=width,
                    height=height,
                ),
            )

    return regions


def compute_region_mean_disparity(
    disparity_frame: np.ndarray,
    region: TrackingRegion,
) -> float:
    """Compute mean non-zero disparity inside a tracking region."""

    roi = disparity_frame[region.y : region.y2, region.x : region.x2]

    if roi.size == 0:
        return 0.0

    valid_pixels = roi[roi > 0]

    if valid_pixels.size == 0:
        return 0.0

    return float(np.mean(valid_pixels))


def score_tracking_regions(
    *,
    disparity_frame: np.ndarray,
    regions: list[TrackingRegion],
) -> list[RegionScore]:
    """Compute mean disparity scores for tracking regions."""

    return [
        RegionScore(
            region=region,
            mean_disparity=compute_region_mean_disparity(
                disparity_frame,
                region,
            ),
        )
        for region in regions
    ]


def find_best_region(
    scores: list[RegionScore],
) -> RegionScore | None:
    """Return the region with the highest mean disparity."""

    if not scores:
        return None

    return max(scores, key=lambda score: score.mean_disparity)


def find_closest_object_region(
    *,
    disparity_frame: np.ndarray,
    rows: int = DEFAULT_GRID_ROWS,
    columns: int = DEFAULT_GRID_COLUMNS,
    min_mean_disparity: float = DEFAULT_MIN_MEAN_DISPARITY,
) -> ClosestObjectResult:
    """Find the grid region most likely to contain the closest object."""

    frame_height, frame_width = disparity_frame.shape[:2]

    regions = create_tracking_grid(
        frame_width=frame_width,
        frame_height=frame_height,
        rows=rows,
        columns=columns,
    )
    scores = score_tracking_regions(
        disparity_frame=disparity_frame,
        regions=regions,
    )
    best_score = find_best_region(scores)

    if best_score is None or best_score.mean_disparity < min_mean_disparity:
        return ClosestObjectResult(
            region=None,
            mean_disparity=0.0,
            detected=False,
        )

    return ClosestObjectResult(
        region=best_score.region,
        mean_disparity=best_score.mean_disparity,
        detected=True,
    )


def scale_region(
    *,
    region: TrackingRegion,
    source_width: int,
    source_height: int,
    target_width: int,
    target_height: int,
) -> TrackingRegion:
    """Scale a region from one frame size to another."""

    if source_width <= 0 or source_height <= 0:
        msg = "source dimensions must be positive"
        raise ValueError(msg)

    if target_width <= 0 or target_height <= 0:
        msg = "target dimensions must be positive"
        raise ValueError(msg)

    scale_x = target_width / source_width
    scale_y = target_height / source_height

    return TrackingRegion(
        x=round(region.x * scale_x),
        y=round(region.y * scale_y),
        width=round(region.width * scale_x),
        height=round(region.height * scale_y),
    )


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


def get_proximity_level_rank(proximity_level: ProximityLevel) -> int:
    """Return numeric rank for comparing proximity levels."""

    ranks = {
        ProximityLevel.SAFE: 0,
        ProximityLevel.NEAR: 1,
        ProximityLevel.VERY_CLOSE: 2,
    }

    return ranks[proximity_level]


def get_tracker_message(
    *,
    detected: bool,
    proximity_level: ProximityLevel,
) -> str:
    """Return a short HUD message for the tracker state."""

    if not detected:
        return "No close object detected."

    messages = {
        ProximityLevel.SAFE: "Closest object detected, but still far away.",
        ProximityLevel.NEAR: "Closest object is near the camera.",
        ProximityLevel.VERY_CLOSE: "Closest object is very close.",
    }

    return messages[proximity_level]


def update_tracker_stats(
    *,
    stats: TrackerStats,
    result: ClosestObjectResult,
    proximity_level: ProximityLevel,
) -> TrackerStats:
    """Return updated closest object tracker statistics."""

    detection_count = stats.detection_count + int(result.detected)

    if result.detected:
        if stats.max_disparity is None:
            max_disparity = result.mean_disparity
        else:
            max_disparity = max(stats.max_disparity, result.mean_disparity)

        if get_proximity_level_rank(proximity_level) > get_proximity_level_rank(
            stats.peak_level,
        ):
            peak_level = proximity_level
        else:
            peak_level = stats.peak_level
    else:
        max_disparity = stats.max_disparity
        peak_level = stats.peak_level

    return TrackerStats(
        frame_count=stats.frame_count + 1,
        detection_count=detection_count,
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


def draw_tracking_grid(
    frame: np.ndarray,
    *,
    rows: int = DEFAULT_GRID_ROWS,
    columns: int = DEFAULT_GRID_COLUMNS,
) -> None:
    """Draw a subtle tracking grid."""

    height, width = frame.shape[:2]
    regions = create_tracking_grid(
        frame_width=width,
        frame_height=height,
        rows=rows,
        columns=columns,
    )

    for region in regions:
        cv2.rectangle(
            frame,
            (region.x, region.y),
            (region.x2, region.y2),
            (90, 90, 90),
            1,
        )


def draw_detection_region(
    frame: np.ndarray,
    *,
    region: TrackingRegion | None,
    detected: bool,
    proximity_level: ProximityLevel,
    label: str,
) -> None:
    """Draw the currently detected closest region."""

    if not detected or region is None:
        return

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
        (region.x + 10, max(30, region.y + 30)),
        scale=0.65,
        color=color,
        thickness=2,
    )


def draw_rgb_hud(
    frame: np.ndarray,
    *,
    result: ClosestObjectResult,
    proximity_level: ProximityLevel,
    stats: TrackerStats,
) -> None:
    """Draw user-facing tracker information on the RGB frame."""

    detection_ratio = 0.0
    if stats.frame_count > 0:
        detection_ratio = stats.detection_count / stats.frame_count

    lines = [
        "Closest Object Tracker",
        f"Detected: {result.detected}",
        f"Mean disparity: {result.mean_disparity:.1f}",
        f"Proximity: {proximity_level.value}",
        f"Frames: {stats.frame_count}",
        f"Detections: {stats.detection_count}",
        f"Detection ratio: {detection_ratio:.2f}",
        f"Max disparity: {format_optional_disparity(stats.max_disparity)}",
        f"Peak level: {stats.peak_level.value}",
        get_tracker_message(
            detected=result.detected,
            proximity_level=proximity_level,
        ),
        "R - reset stats | Q / ESC - quit",
    ]

    x = 20
    y = 34

    for index, line in enumerate(lines):
        draw_text(
            frame,
            line,
            (x, y + index * 27),
            scale=0.58,
            color=(255, 255, 255),
            thickness=1,
        )


def draw_disparity_hud(
    frame: np.ndarray,
    *,
    result: ClosestObjectResult,
    max_disparity: float,
) -> None:
    """Draw measurement/debug tracker information on the disparity frame."""

    normalized_value = normalize_disparity_value(
        mean_disparity=result.mean_disparity,
        max_disparity=max_disparity,
    )

    lines = [
        "Disparity tracking view",
        f"Grid: {DEFAULT_GRID_ROWS} x {DEFAULT_GRID_COLUMNS}",
        f"Max disparity: {max_disparity:.1f}",
        f"Normalized: {normalized_value:.2f}",
    ]

    x = 20
    y = 34

    for index, line in enumerate(lines):
        draw_text(
            frame,
            line,
            (x, y + index * 27),
            scale=0.58,
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
    """Run the OAK-D closest object tracker demo."""

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

        stats = TrackerStats()

        while True:
            rgb_message = rgb_queue.get()
            disparity_message = disparity_queue.get()

            rgb_frame = rgb_message.getCvFrame()
            disparity_frame = disparity_message.getFrame()

            disparity_height, disparity_width = disparity_frame.shape[:2]
            rgb_height, rgb_width = rgb_frame.shape[:2]

            result = find_closest_object_region(
                disparity_frame=disparity_frame,
            )
            proximity_level = classify_proximity(
                mean_disparity=result.mean_disparity,
                near_threshold=DEFAULT_NEAR_THRESHOLD,
                very_close_threshold=DEFAULT_VERY_CLOSE_THRESHOLD,
            )

            stats = update_tracker_stats(
                stats=stats,
                result=result,
                proximity_level=proximity_level,
            )

            rgb_region = None
            if result.region is not None:
                rgb_region = scale_region(
                    region=result.region,
                    source_width=disparity_width,
                    source_height=disparity_height,
                    target_width=rgb_width,
                    target_height=rgb_height,
                )

            colorized_disparity = colorize_disparity_frame(
                disparity_frame,
                max_disparity=max_disparity,
            )

            draw_tracking_grid(colorized_disparity)
            draw_detection_region(
                colorized_disparity,
                region=result.region,
                detected=result.detected,
                proximity_level=proximity_level,
                label="CLOSEST",
            )
            draw_detection_region(
                rgb_frame,
                region=rgb_region,
                detected=result.detected,
                proximity_level=proximity_level,
                label="TRACKED REGION",
            )
            draw_rgb_hud(
                rgb_frame,
                result=result,
                proximity_level=proximity_level,
                stats=stats,
            )
            draw_disparity_hud(
                colorized_disparity,
                result=result,
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
                stats = TrackerStats()

    cv2.destroyWindow(WINDOW_NAME)


if __name__ == "__main__":
    run()
