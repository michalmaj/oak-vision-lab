import numpy as np
import pytest

from oak_vision_lab.depth.disparity import (
    compute_mean_disparity,
    normalize_disparity_frame,
)


def test_normalize_disparity_frame_returns_uint8_frame() -> None:
    disparity_frame = np.array([[0, 48, 96]], dtype=np.uint8)

    normalized_frame = normalize_disparity_frame(disparity_frame, max_disparity=96.0)

    assert normalized_frame.dtype == np.uint8
    assert normalized_frame.tolist() == [[0, 127, 255]]


def test_normalize_disparity_frame_clips_values() -> None:
    disparity_frame = np.array([[0, 96, 192]], dtype=np.uint8)

    normalized_frame = normalize_disparity_frame(disparity_frame, max_disparity=96.0)

    assert normalized_frame.tolist() == [[0, 255, 255]]


def test_normalize_disparity_frame_rejects_invalid_max_disparity() -> None:
    disparity_frame = np.array([[0, 1, 2]], dtype=np.uint8)

    with pytest.raises(ValueError, match="max_disparity must be greater than zero"):
        normalize_disparity_frame(disparity_frame, max_disparity=0.0)


def test_compute_mean_disparity_ignores_zero_values() -> None:
    frame = np.array([[0, 10, 20], [0, 0, 30]], dtype=np.uint8)

    mean_disparity = compute_mean_disparity(frame)

    assert mean_disparity == 20.0


def test_compute_mean_disparity_returns_zero_when_no_valid_pixels_exist() -> None:
    frame = np.zeros((4, 4), dtype=np.uint8)

    mean_disparity = compute_mean_disparity(frame)

    assert mean_disparity == 0.0
