import numpy as np
import pytest

from oak_vision_lab.demos.depth_proximity_alert import extract_center_roi
from oak_vision_lab.depth.disparity import (
    compute_mean_disparity,
    normalize_disparity_frame,
)
from oak_vision_lab.depth.proximity import (
    ProximityLevel,
    classify_proximity,
)


def test_normalize_disparity_frame_returns_uint8_frame() -> None:
    disparity_frame = np.array([[0, 48, 96]], dtype=np.uint8)

    normalized_frame = normalize_disparity_frame(disparity_frame, max_disparity=96.0)

    assert normalized_frame.dtype == np.uint8
    assert normalized_frame.tolist() == [[0, 127, 255]]


def test_extract_center_roi_returns_expected_shape() -> None:
    frame = np.zeros((100, 200), dtype=np.uint8)

    roi = extract_center_roi(frame, roi_scale=0.5)

    assert roi.shape == (50, 100)


def test_extract_center_roi_rejects_invalid_scale() -> None:
    frame = np.zeros((100, 200), dtype=np.uint8)

    with pytest.raises(ValueError, match=r"roi_scale must be in the range"):
        extract_center_roi(frame, roi_scale=0.0)


def test_compute_mean_disparity_ignores_zero_values() -> None:
    frame = np.array([[0, 10, 20], [0, 0, 30]], dtype=np.uint8)

    mean_disparity = compute_mean_disparity(frame)

    assert mean_disparity == 20.0


def test_compute_mean_disparity_returns_zero_for_empty_valid_pixels() -> None:
    frame = np.zeros((4, 4), dtype=np.uint8)

    mean_disparity = compute_mean_disparity(frame)

    assert mean_disparity == 0.0


@pytest.mark.parametrize(
    ("mean_disparity", "expected_level"),
    [
        (10.0, ProximityLevel.SAFE),
        (25.0, ProximityLevel.NEAR),
        (44.9, ProximityLevel.NEAR),
        (45.0, ProximityLevel.VERY_CLOSE),
    ],
)
def test_classify_proximity_returns_expected_level(
    mean_disparity: float,
    expected_level: ProximityLevel,
) -> None:
    level = classify_proximity(
        mean_disparity,
        near_threshold=25.0,
        very_close_threshold=45.0,
    )

    assert level is expected_level


def test_classify_proximity_rejects_invalid_threshold_order() -> None:
    with pytest.raises(
        ValueError,
        match="very_close_threshold must be greater than near_threshold",
    ):
        classify_proximity(
            mean_disparity=10.0,
            near_threshold=30.0,
            very_close_threshold=20.0,
        )
