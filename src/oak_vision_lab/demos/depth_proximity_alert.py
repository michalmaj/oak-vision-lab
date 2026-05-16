"""OAK-D depth proximity alert demo using DepthAI v2 API."""

from __future__ import annotations

import time
from enum import Enum

import cv2
import depthai as dai
import numpy as np
from numpy.typing import NDArray

from oak_vision_lab.visualization.hud import HudConfig, build_hud_lines


class ProximityLevel(Enum):
    """Detected proximity level based on disparity statistics."""

    SAFE = "SAFE"
    NEAR = "NEAR"
    VERY_CLOSE = "VERY CLOSE"


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


def normalize_disparity_frame(
    disparity_frame: NDArray[np.uint8],
    max_disparity: float,
) -> NDArray[np.uint8]:
    """Normalize a raw disparity frame to the 0-255 range for visualization."""

    if max_disparity <= 0.0:
        msg = "max_disparity must be greater than zero"
        raise ValueError(msg)

    normalized_frame = disparity_frame.astype(np.float32) * (255.0 / max_disparity)
    normalized_frame = np.clip(normalized_frame, 0, 255)

    return normalized_frame.astype(np.uint8)


def colorize_disparity_frame(
    disparity_frame: NDArray[np.uint8],
    max_disparity: float,
) -> NDArray[np.uint8]:
    """Convert a raw disparity frame into a colorful OpenCV visualization."""

    normalized_frame = normalize_disparity_frame(disparity_frame, max_disparity)

    return cv2.applyColorMap(normalized_frame, cv2.COLORMAP_JET)


def extract_center_roi(
    frame: NDArray[np.uint8],
    roi_scale: float = 0.25,
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


def compute_mean_disparity(frame: NDArray[np.uint8]) -> float:
    """Compute the mean disparity while ignoring zero values."""

    valid_pixels = frame[frame > 0]

    if valid_pixels.size == 0:
        return 0.0

    return float(np.mean(valid_pixels))


def classify_proximity(
    mean_disparity: float,
    near_threshold: float,
    very_close_threshold: float,
) -> ProximityLevel:
    """Classify proximity based on mean disparity.

    Higher disparity usually means that an object is closer to the camera.
    """

    if near_threshold < 0.0 or very_close_threshold < 0.0:
        msg = "thresholds must be non-negative"
        raise ValueError(msg)

    if very_close_threshold <= near_threshold:
        msg = "very_close_threshold must be greater than near_threshold"
        raise ValueError(msg)

    if mean_disparity >= very_close_threshold:
        return ProximityLevel.VERY_CLOSE

    if mean_disparity >= near_threshold:
        return ProximityLevel.NEAR

    return ProximityLevel.SAFE


def get_alert_color(level: ProximityLevel) -> tuple[int, int, int]:
    """Return an OpenCV BGR color for a proximity level."""

    if level is ProximityLevel.VERY_CLOSE:
        return (0, 0, 255)

    if level is ProximityLevel.NEAR:
        return (0, 165, 255)

    return (0, 255, 0)


def draw_center_roi(
    frame: NDArray[np.uint8],
    roi_scale: float,
    color: tuple[int, int, int],
) -> None:
    """Draw the centered region of interest on the frame."""

    height, width = frame.shape[:2]

    roi_width = max(1, int(width * roi_scale))
    roi_height = max(1, int(height * roi_scale))

    x1 = (width - roi_width) // 2
    y1 = (height - roi_height) // 2
    x2 = x1 + roi_width
    y2 = y1 + roi_height

    cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness=2)


def draw_alert_border(
    frame: NDArray[np.uint8],
    level: ProximityLevel,
) -> None:
    """Draw a colored alert border around the frame."""

    color = get_alert_color(level)
    thickness = 8 if level is ProximityLevel.VERY_CLOSE else 4

    cv2.rectangle(
        frame,
        (0, 0),
        (frame.shape[1] - 1, frame.shape[0] - 1),
        color,
        thickness=thickness,
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
            (origin_x * 0, 0, 0),
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


def run_depth_proximity_alert() -> None:
    """Run the interactive depth proximity alert demo."""

    print(f"DepthAI: {dai.__version__}")

    roi_scale = 0.25
    near_threshold = 25.0
    very_close_threshold = 45.0

    hud_config = HudConfig(title="oak-vision-lab | Depth Proximity Alert")
    show_help = True

    previous_time = time.perf_counter()
    fps = 0.0

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
            message = disparity_queue.get()
            disparity_frame = message.getFrame()

            center_roi = extract_center_roi(disparity_frame, roi_scale=roi_scale)
            mean_disparity = compute_mean_disparity(center_roi)
            proximity_level = classify_proximity(
                mean_disparity,
                near_threshold=near_threshold,
                very_close_threshold=very_close_threshold,
            )

            colorized_frame = colorize_disparity_frame(disparity_frame, max_disparity)
            alert_color = get_alert_color(proximity_level)

            draw_center_roi(colorized_frame, roi_scale=roi_scale, color=alert_color)
            draw_alert_border(colorized_frame, proximity_level)

            current_time = time.perf_counter()
            delta_time = current_time - previous_time
            previous_time = current_time

            if delta_time > 0.0:
                fps = 1.0 / delta_time

            active_config = HudConfig(
                title=hud_config.title,
                show_fps=True,
                show_help=show_help,
                show_status=True,
            )

            hud_lines = build_hud_lines(
                active_config,
                fps=fps,
                status=f"{proximity_level.value}\
                      | mean disparity: {mean_disparity:.1f}",
            )

            draw_hud(colorized_frame, hud_lines)

            cv2.imshow("oak-vision-lab | Depth Proximity Alert", colorized_frame)

            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                break

            if key == ord("h"):
                show_help = not show_help

    cv2.destroyAllWindows()


if __name__ == "__main__":
    run_depth_proximity_alert()
