"""OAK-D RGB and depth-like split-screen demo using DepthAI v2 API."""

from __future__ import annotations

import time

import cv2
import depthai as dai
import numpy as np
from numpy.typing import NDArray

from oak_vision_lab.visualization.hud import HudConfig, build_hud_lines


def get_camera_socket(name: str, fallback_name: str) -> dai.CameraBoardSocket:
    """Get a camera socket while supporting older and newer DepthAI naming styles."""

    if hasattr(dai.CameraBoardSocket, name):
        return getattr(dai.CameraBoardSocket, name)

    return getattr(dai.CameraBoardSocket, fallback_name)


def create_rgb_depth_pipeline() -> tuple[dai.Pipeline, float]:
    """Create a DepthAI v2 pipeline with RGB preview and stereo disparity output."""

    pipeline = dai.Pipeline()

    color_camera = pipeline.create(dai.node.ColorCamera)
    left_camera = pipeline.create(dai.node.MonoCamera)
    right_camera = pipeline.create(dai.node.MonoCamera)
    stereo = pipeline.create(dai.node.StereoDepth)

    rgb_output = pipeline.create(dai.node.XLinkOut)
    disparity_output = pipeline.create(dai.node.XLinkOut)

    rgb_output.setStreamName("rgb")
    disparity_output.setStreamName("disparity")

    rgb_socket = (
        dai.CameraBoardSocket.RGB
        if hasattr(dai.CameraBoardSocket, "RGB")
        else dai.CameraBoardSocket.CAM_A
    )

    color_camera.setBoardSocket(rgb_socket)
    color_camera.setResolution(dai.ColorCameraProperties.SensorResolution.THE_1080_P)
    color_camera.setPreviewSize(640, 400)
    color_camera.setInterleaved(False)
    color_camera.setColorOrder(dai.ColorCameraProperties.ColorOrder.BGR)
    color_camera.setFps(30)

    left_camera.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)
    right_camera.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)

    left_camera.setBoardSocket(get_camera_socket("LEFT", "CAM_B"))
    right_camera.setBoardSocket(get_camera_socket("RIGHT", "CAM_C"))

    stereo.setDefaultProfilePreset(dai.node.StereoDepth.PresetMode.HIGH_DENSITY)
    stereo.setLeftRightCheck(True)
    stereo.setExtendedDisparity(False)
    stereo.setSubpixel(False)

    color_camera.preview.link(rgb_output.input)
    left_camera.out.link(stereo.left)
    right_camera.out.link(stereo.right)
    stereo.disparity.link(disparity_output.input)

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


def resize_to_height(frame: NDArray[np.uint8], target_height: int) -> NDArray[np.uint8]:
    """Resize a frame while preserving its aspect ratio."""

    if target_height <= 0:
        msg = "target_height must be greater than zero"
        raise ValueError(msg)

    height, width = frame.shape[:2]

    if height <= 0:
        msg = "frame height must be greater than zero"
        raise ValueError(msg)

    scale = target_height / height
    target_width = int(width * scale)

    return cv2.resize(frame, (target_width, target_height))


def create_labeled_panel(
    frame: NDArray[np.uint8],
    label: str,
) -> NDArray[np.uint8]:
    """Create a labeled image panel for split-screen visualization."""

    panel = frame.copy()

    cv2.rectangle(panel, (0, 0), (panel.shape[1], 45), (0, 0, 0), thickness=-1)
    cv2.putText(
        panel,
        label,
        (20, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 255, 255),
        2,
        cv2.LINE_AA,
    )

    return panel


def create_split_screen(
    rgb_frame: NDArray[np.uint8],
    disparity_frame: NDArray[np.uint8],
    max_disparity: float,
) -> NDArray[np.uint8]:
    """Create a side-by-side RGB and colorized disparity visualization."""

    colorized_disparity = colorize_disparity_frame(disparity_frame, max_disparity)
    colorized_disparity = resize_to_height(colorized_disparity, rgb_frame.shape[0])

    rgb_panel = create_labeled_panel(rgb_frame, "RGB camera")
    disparity_panel = create_labeled_panel(colorized_disparity, "Stereo disparity")

    return np.hstack((rgb_panel, disparity_panel))


def draw_hud(
    frame: NDArray[np.uint8],
    lines: list[str],
    *,
    origin_x: int = 20,
    origin_y: int = 80,
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


def run_rgb_depth_split_screen() -> None:
    """Run the interactive RGB and depth-like split-screen demo."""

    print(f"DepthAI: {dai.__version__}")

    hud_config = HudConfig(title="oak-vision-lab | RGB + Depth Split-Screen")
    show_help = True

    previous_time = time.perf_counter()
    fps = 0.0

    pipeline, max_disparity = create_rgb_depth_pipeline()

    with dai.Device(pipeline) as device:
        print(f"MXID: {device.getMxId()}")
        print(f"Connected cameras: {device.getConnectedCameras()}")
        print(f"USB speed: {device.getUsbSpeed()}")

        rgb_queue = device.getOutputQueue(name="rgb", maxSize=4, blocking=False)
        disparity_queue = device.getOutputQueue(
            name="disparity",
            maxSize=4,
            blocking=False,
        )

        while True:
            rgb_message = rgb_queue.get()
            disparity_message = disparity_queue.get()

            rgb_frame = rgb_message.getCvFrame()
            disparity_frame = disparity_message.getFrame()

            split_screen = create_split_screen(
                rgb_frame,
                disparity_frame,
                max_disparity,
            )

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
                status="RGB and stereo disparity streams active",
            )

            draw_hud(split_screen, hud_lines)

            cv2.imshow("oak-vision-lab | RGB + Depth Split-Screen", split_screen)

            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                break

            if key == ord("h"):
                show_help = not show_help

    cv2.destroyAllWindows()


if __name__ == "__main__":
    run_rgb_depth_split_screen()
