import numpy as np
import pytest

from oak_vision_lab.demos.depth_music_playground import (
    MusicPlaygroundState,
    MusicZone,
    ZoneMeasurement,
    compute_zone_mean_disparity,
    create_music_zones,
    create_note_triggers,
    get_music_message,
    get_zone_intensity,
    is_zone_active,
    measure_music_zones,
    scale_music_zone,
    scale_music_zones,
    should_trigger_note,
    update_music_state,
)
from oak_vision_lab.depth.proximity import ProximityLevel


def test_create_music_zones_returns_one_zone_per_note() -> None:
    zones = create_music_zones(
        frame_width=100,
        frame_height=80,
        notes=("C", "D", "E", "G", "A"),
    )

    assert len(zones) == 5
    assert zones[0].note == "C"
    assert zones[-1].note == "A"


def test_create_music_zones_covers_frame_width_with_remainder() -> None:
    zones = create_music_zones(
        frame_width=103,
        frame_height=80,
        notes=("C", "D", "E", "G", "A"),
    )

    assert zones[0] == MusicZone(index=0, note="C", x=0, y=20, width=20, height=50)
    assert zones[-1].x2 == 103


def test_create_music_zones_rejects_invalid_frame_dimensions() -> None:
    with pytest.raises(ValueError, match="frame dimensions must be positive"):
        create_music_zones(frame_width=0, frame_height=80)


def test_create_music_zones_rejects_empty_notes() -> None:
    with pytest.raises(ValueError, match="notes must not be empty"):
        create_music_zones(frame_width=100, frame_height=80, notes=())


def test_create_music_zones_rejects_invalid_usable_height() -> None:
    with pytest.raises(ValueError, match="usable zone height must be positive"):
        create_music_zones(
            frame_width=100,
            frame_height=80,
            top_margin_ratio=0.9,
            bottom_margin_ratio=0.2,
        )


def test_compute_zone_mean_disparity_ignores_zero_values() -> None:
    frame = np.array(
        [
            [0, 0, 0, 0],
            [0, 10, 20, 0],
            [0, 30, 40, 0],
            [0, 0, 0, 0],
        ],
        dtype=np.uint8,
    )
    zone = MusicZone(index=0, note="C", x=1, y=1, width=2, height=2)

    result = compute_zone_mean_disparity(frame, zone)

    assert result == 25.0


def test_compute_zone_mean_disparity_returns_zero_without_valid_pixels() -> None:
    frame = np.zeros((4, 4), dtype=np.uint8)
    zone = MusicZone(index=0, note="C", x=1, y=1, width=2, height=2)

    result = compute_zone_mean_disparity(frame, zone)

    assert result == 0.0


def test_is_zone_active_returns_true_for_near_and_very_close() -> None:
    assert is_zone_active(ProximityLevel.NEAR)
    assert is_zone_active(ProximityLevel.VERY_CLOSE)


def test_is_zone_active_returns_false_for_safe() -> None:
    assert not is_zone_active(ProximityLevel.SAFE)


def test_should_trigger_note_allows_first_trigger() -> None:
    result = should_trigger_note(
        zone_index=0,
        current_time=10.0,
        last_trigger_time_by_zone={},
    )

    assert result


def test_should_trigger_note_rejects_trigger_inside_cooldown() -> None:
    result = should_trigger_note(
        zone_index=0,
        current_time=10.2,
        last_trigger_time_by_zone={0: 10.0},
        cooldown_seconds=0.35,
    )

    assert not result


def test_should_trigger_note_allows_trigger_after_cooldown() -> None:
    result = should_trigger_note(
        zone_index=0,
        current_time=10.4,
        last_trigger_time_by_zone={0: 10.0},
        cooldown_seconds=0.35,
    )

    assert result


def test_should_trigger_note_rejects_negative_cooldown() -> None:
    with pytest.raises(ValueError, match="cooldown_seconds must be non-negative"):
        should_trigger_note(
            zone_index=0,
            current_time=10.0,
            last_trigger_time_by_zone={},
            cooldown_seconds=-1.0,
        )


def test_create_note_triggers_returns_trigger_for_active_zone() -> None:
    zone = MusicZone(index=0, note="C", x=0, y=0, width=10, height=10)
    measurements = [
        ZoneMeasurement(
            zone=zone,
            mean_disparity=30.0,
            proximity_level=ProximityLevel.NEAR,
            active=True,
        ),
    ]

    triggers = create_note_triggers(
        measurements=measurements,
        current_time=10.0,
        last_trigger_time_by_zone={},
    )

    assert len(triggers) == 1
    assert triggers[0].note == "C"
    assert triggers[0].zone_index == 0


def test_create_note_triggers_skips_inactive_zone() -> None:
    zone = MusicZone(index=0, note="C", x=0, y=0, width=10, height=10)
    measurements = [
        ZoneMeasurement(
            zone=zone,
            mean_disparity=0.0,
            proximity_level=ProximityLevel.SAFE,
            active=False,
        ),
    ]

    triggers = create_note_triggers(
        measurements=measurements,
        current_time=10.0,
        last_trigger_time_by_zone={},
    )

    assert triggers == []


def test_update_music_state_records_triggers() -> None:
    zone = MusicZone(index=1, note="D", x=0, y=0, width=10, height=10)
    measurements = [
        ZoneMeasurement(
            zone=zone,
            mean_disparity=40.0,
            proximity_level=ProximityLevel.VERY_CLOSE,
            active=True,
        ),
    ]
    triggers = create_note_triggers(
        measurements=measurements,
        current_time=12.0,
        last_trigger_time_by_zone={},
    )

    state = update_music_state(
        state=MusicPlaygroundState(),
        triggers=triggers,
    )

    assert state.total_triggers == 1
    assert state.last_trigger_time_by_zone == {1: 12.0}
    assert state.last_note == "D"


def test_update_music_state_preserves_existing_trigger_times() -> None:
    state = MusicPlaygroundState(
        total_triggers=1,
        last_trigger_time_by_zone={0: 10.0},
        last_note="C",
    )

    updated = update_music_state(state=state, triggers=[])

    assert updated.total_triggers == 1
    assert updated.last_trigger_time_by_zone == {0: 10.0}
    assert updated.last_note == "C"


def test_get_zone_intensity_returns_normalized_value() -> None:
    result = get_zone_intensity(mean_disparity=25.0, max_disparity=100.0)

    assert result == 0.25


def test_get_zone_intensity_clamps_to_one() -> None:
    result = get_zone_intensity(mean_disparity=150.0, max_disparity=100.0)

    assert result == 1.0


def test_get_zone_intensity_handles_invalid_max_disparity() -> None:
    result = get_zone_intensity(mean_disparity=25.0, max_disparity=0.0)

    assert result == 0.0


def test_get_music_message_returns_triggered_notes() -> None:
    zone = MusicZone(index=0, note="C", x=0, y=0, width=10, height=10)
    measurements = [
        ZoneMeasurement(
            zone=zone,
            mean_disparity=30.0,
            proximity_level=ProximityLevel.NEAR,
            active=True,
        ),
    ]
    triggers = create_note_triggers(
        measurements=measurements,
        current_time=10.0,
        last_trigger_time_by_zone={},
    )

    message = get_music_message(
        triggers=triggers,
        state=MusicPlaygroundState(),
    )

    assert message == "Triggered: C"


def test_get_music_message_returns_last_note() -> None:
    message = get_music_message(
        triggers=[],
        state=MusicPlaygroundState(last_note="D"),
    )

    assert message == "Last note: D"


def test_get_music_message_returns_instruction() -> None:
    message = get_music_message(
        triggers=[],
        state=MusicPlaygroundState(),
    )

    assert "Move a hand" in message


def test_measure_music_zones_returns_measurements_for_each_zone() -> None:
    frame = np.zeros((4, 4), dtype=np.uint8)
    frame[:, :2] = 10
    frame[:, 2:] = 50
    zones = [
        MusicZone(index=0, note="C", x=0, y=0, width=2, height=4),
        MusicZone(index=1, note="D", x=2, y=0, width=2, height=4),
    ]

    measurements = measure_music_zones(
        disparity_frame=frame,
        zones=zones,
    )

    assert len(measurements) == 2
    assert measurements[0].mean_disparity == 10.0
    assert measurements[1].mean_disparity == 50.0
    assert not measurements[0].active
    assert measurements[1].active


def test_scale_music_zone_scales_coordinates_between_frame_sizes() -> None:
    zone = MusicZone(index=0, note="C", x=10, y=20, width=30, height=40)

    scaled = scale_music_zone(
        zone=zone,
        source_width=100,
        source_height=200,
        target_width=200,
        target_height=100,
    )

    assert scaled == MusicZone(
        index=0,
        note="C",
        x=20,
        y=10,
        width=60,
        height=20,
    )


def test_scale_music_zone_rejects_invalid_source_dimensions() -> None:
    with pytest.raises(ValueError, match="source dimensions must be positive"):
        scale_music_zone(
            zone=MusicZone(index=0, note="C", x=0, y=0, width=10, height=10),
            source_width=0,
            source_height=100,
            target_width=100,
            target_height=100,
        )


def test_scale_music_zone_rejects_invalid_target_dimensions() -> None:
    with pytest.raises(ValueError, match="target dimensions must be positive"):
        scale_music_zone(
            zone=MusicZone(index=0, note="C", x=0, y=0, width=10, height=10),
            source_width=100,
            source_height=100,
            target_width=0,
            target_height=100,
        )


def test_scale_music_zones_scales_multiple_zones() -> None:
    zones = [
        MusicZone(index=0, note="C", x=0, y=0, width=10, height=10),
        MusicZone(index=1, note="D", x=10, y=0, width=10, height=10),
    ]

    scaled = scale_music_zones(
        zones=zones,
        source_width=20,
        source_height=10,
        target_width=40,
        target_height=20,
    )

    assert scaled == [
        MusicZone(index=0, note="C", x=0, y=0, width=20, height=20),
        MusicZone(index=1, note="D", x=20, y=0, width=20, height=20),
    ]
