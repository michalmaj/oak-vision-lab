"""Reusable DepthAI camera pipeline helpers."""

from __future__ import annotations

import depthai as dai


def get_camera_socket(name: str, fallback_name: str) -> dai.CameraBoardSocket:
    """Get a camera socket while supporting older and newer DepthAI naming styles."""

    if hasattr(dai.CameraBoardSocket, name):
        return getattr(dai.CameraBoardSocket, name)

    return getattr(dai.CameraBoardSocket, fallback_name)


def create_stereo_disparity_pipeline(
    *,
    stream_name: str = "disparity",
) -> tuple[dai.Pipeline, float]:
    """Create a reusable DepthAI v2 stereo disparity pipeline."""

    pipeline = dai.Pipeline()

    left_camera = pipeline.create(dai.node.MonoCamera)
    right_camera = pipeline.create(dai.node.MonoCamera)
    stereo = pipeline.create(dai.node.StereoDepth)
    output = pipeline.create(dai.node.XLinkOut)

    output.setStreamName(stream_name)

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
