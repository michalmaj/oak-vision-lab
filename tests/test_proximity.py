import pytest

from oak_vision_lab.depth.proximity import (
    ProximityLevel,
    classify_proximity,
    get_alert_color,
)


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


def test_classify_proximity_rejects_negative_thresholds() -> None:
    with pytest.raises(ValueError, match="thresholds must be non-negative"):
        classify_proximity(
            mean_disparity=10.0,
            near_threshold=-1.0,
            very_close_threshold=45.0,
        )


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


def test_get_alert_color_returns_safe_color() -> None:
    assert get_alert_color(ProximityLevel.SAFE) == (0, 255, 0)


def test_get_alert_color_returns_near_color() -> None:
    assert get_alert_color(ProximityLevel.NEAR) == (0, 165, 255)


def test_get_alert_color_returns_very_close_color() -> None:
    assert get_alert_color(ProximityLevel.VERY_CLOSE) == (0, 0, 255)
