import numpy as np
import pytest

from oak_vision_lab.demos.rgb_depth_split_screen import resize_to_height
from oak_vision_lab.depth.disparity import normalize_disparity_frame


def test_normalize_disparity_frame_returns_uint8_frame() -> None:
    disparity_frame = np.array([[0, 48, 96]], dtype=np.uint8)

    normalized_frame = normalize_disparity_frame(disparity_frame, max_disparity=96.0)

    assert normalized_frame.dtype == np.uint8
    assert normalized_frame.tolist() == [[0, 127, 255]]


def test_normalize_disparity_frame_clips_values() -> None:
    disparity_frame = np.array([[0, 96, 192]], dtype=np.uint8)

    normalized_frame = normalize_disparity_frame(disparity_frame, max_disparity=96.0)

    assert normalized_frame.tolist() == [[0, 255, 255]]


def test_resize_to_height_preserves_aspect_ratio() -> None:
    frame = np.zeros((100, 200, 3), dtype=np.uint8)

    resized_frame = resize_to_height(frame, target_height=50)

    assert resized_frame.shape == (50, 100, 3)


def test_resize_to_height_rejects_invalid_height() -> None:
    frame = np.zeros((100, 200, 3), dtype=np.uint8)

    with pytest.raises(ValueError, match="target_height must be greater than zero"):
        resize_to_height(frame, target_height=0)
