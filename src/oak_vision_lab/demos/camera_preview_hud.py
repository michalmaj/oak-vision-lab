"""OAK-D camera preview demo with a colorful HUD using DepthAI v2 API."""

from __future__ import annotations

import time

import cv2
import depthai as dai

from oak_vision_lab.visualization.hud import HudConfig, build_hud_lines


def create_color_camera_pipeline() -> dai.Pipeline:
    """Create a DepthAI v2 RGB preview pipeline."""

    pipeline = dai.Pipeline()

    color_camera = pipeline.create(dai.node.ColorCamera)

    rgb_socket = (
        dai.CameraBoardSocket.RGB
        if hasattr(dai.CameraBoardSocket, "RGB")
        else dai.CameraBoardSocket.CAM_A
    )

    color_camera.setBoardSocket(rgb_socket)
    color_camera.setResolution(dai.ColorCameraProperties.SensorResolution.THE_1080_P)
    color_camera.setPreviewSize(1280, 720)
    color_camera.setInterleaved(False)
    color_camera.setColorOrder(dai.ColorCameraProperties.ColorOrder.BGR)
    color_camera.setFps(30)

    output = pipeline.create(dai.node.XLinkOut)
    output.setStreamName("preview")

    color_camera.preview.link(output.input)

    return pipeline


def draw_hud(
    frame,
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


def run_camera_preview_hud() -> None:
    """Run the interactive OAK-D preview demo using DepthAI v2."""

    print(f"DepthAI: {dai.__version__}")

    hud_config = HudConfig(title="oak-vision-lab | OAK-D Camera Preview | DepthAI v2")
    show_help = True

    previous_time = time.perf_counter()
    fps = 0.0

    pipeline = create_color_camera_pipeline()

    with dai.Device(pipeline) as device:
        print(f"MXID: {device.getMxId()}")
        print(f"Connected cameras: {device.getConnectedCameras()}")
        print(f"USB speed: {device.getUsbSpeed()}")

        preview_queue = device.getOutputQueue(
            name="preview",
            maxSize=4,
            blocking=False,
        )

        while True:
            message = preview_queue.get()
            frame = message.getCvFrame()

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
                status="camera stream active | DepthAI v2",
            )

            draw_hud(frame, hud_lines)

            cv2.imshow("oak-vision-lab | Camera Preview HUD | DepthAI v2", frame)

            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                break

            if key == ord("h"):
                show_help = not show_help

    cv2.destroyAllWindows()


if __name__ == "__main__":
    run_camera_preview_hud()
