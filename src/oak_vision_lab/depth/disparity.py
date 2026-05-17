"""Reusable disparity processing helpers."""

from __future__ import annotations

import cv2
import numpy as np
from numpy.typing import NDArray


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


def compute_mean_disparity(frame: NDArray[np.uint8]) -> float:
    """Compute the mean disparity while ignoring zero values."""

    valid_pixels = frame[frame > 0]

    if valid_pixels.size == 0:
        return 0.0

    return float(np.mean(valid_pixels))
