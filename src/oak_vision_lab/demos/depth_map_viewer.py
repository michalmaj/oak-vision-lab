"""OAK-D depth map viewer demo using DepthAI v2 API."""

from __future__ import annotations

import time

import cv2
import depthai as dai

from oak_vision_lab.depth.camera import create_stereo_disparity_pipeline
from oak_vision_lab.depth.disparity import colorize_disparity_frame
from oak_vision_lab.visualization.hud import HudConfig, build_hud_lines


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


def run_depth_map_viewer() -> None:
    """Run the interactive OAK-D depth map viewer demo."""

    print(f"DepthAI: {dai.__version__}")

    hud_config = HudConfig(title="oak-vision-lab | Depth Map Viewer | DepthAI v2")
    show_help = True

    previous_time = time.perf_counter()
    fps = 0.0

    pipeline, max_disparity = create_stereo_disparity_pipeline()

    with dai.Device(pipeline) as device:
        print(f"MXID: {device.getMxId()}")
        print(f"Connected cameras: {device.getConnectedCameras()}")
        print(f"USB speed: {device.getUsbSpeed()}")
        print(f"Max disparity: {max_disparity}")

        disparity_queue = device.getOutputQueue(
            name="disparity",
            maxSize=4,
            blocking=False,
        )

        while True:
            message = disparity_queue.get()
            disparity_frame = message.getFrame()
            colorized_frame = colorize_disparity_frame(disparity_frame, max_disparity)

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
                status="stereo disparity stream active | DepthAI v2",
            )

            draw_hud(colorized_frame, hud_lines)

            cv2.imshow(
                "oak-vision-lab | Depth Map Viewer | DepthAI v2", colorized_frame
            )

            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                break

            if key == ord("h"):
                show_help = not show_help

    cv2.destroyAllWindows()


if __name__ == "__main__":
    run_depth_map_viewer()
