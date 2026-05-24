import pytest

from oak_vision_lab.demos.virtual_depth_piano import (
    Fingertip,
    PianoPoint,
    PianoState,
    create_piano_triggers,
    create_virtual_piano_keys,
    find_hovered_key,
    get_piano_message,
    get_pressed_key_indexes,
    is_point_inside_key,
    is_point_inside_polygon,
    is_point_on_segment,
    update_piano_state,
)


def test_create_virtual_piano_keys_returns_one_key_per_note() -> None:
    keys = create_virtual_piano_keys(
        frame_width=100,
        frame_height=100,
        notes=("C", "D", "E"),
    )

    assert len(keys) == 3
    assert keys[0].note == "C"
    assert keys[-1].note == "E"


def test_create_virtual_piano_keys_creates_perspective_shape() -> None:
    keys = create_virtual_piano_keys(
        frame_width=100,
        frame_height=100,
        notes=("C", "D"),
        top_y_ratio=0.5,
        bottom_y_ratio=0.9,
        back_width_ratio=0.6,
        front_width_ratio=1.0,
    )

    assert keys[0].points == (
        PianoPoint(x=20, y=50),
        PianoPoint(x=50, y=50),
        PianoPoint(x=50, y=90),
        PianoPoint(x=0, y=90),
    )
    assert keys[1].points == (
        PianoPoint(x=50, y=50),
        PianoPoint(x=80, y=50),
        PianoPoint(x=100, y=90),
        PianoPoint(x=50, y=90),
    )


def test_create_virtual_piano_keys_rejects_invalid_frame_dimensions() -> None:
    with pytest.raises(ValueError, match="frame dimensions must be positive"):
        create_virtual_piano_keys(frame_width=0, frame_height=100)


def test_create_virtual_piano_keys_rejects_empty_notes() -> None:
    with pytest.raises(ValueError, match="notes must not be empty"):
        create_virtual_piano_keys(frame_width=100, frame_height=100, notes=())


def test_create_virtual_piano_keys_rejects_invalid_ratio() -> None:
    with pytest.raises(ValueError, match="top_y_ratio must be in"):
        create_virtual_piano_keys(
            frame_width=100,
            frame_height=100,
            top_y_ratio=0.0,
        )


def test_create_virtual_piano_keys_rejects_inverted_vertical_ratios() -> None:
    with pytest.raises(ValueError, match="top_y_ratio must be smaller"):
        create_virtual_piano_keys(
            frame_width=100,
            frame_height=100,
            top_y_ratio=0.9,
            bottom_y_ratio=0.5,
        )


def test_create_virtual_piano_keys_rejects_inverted_width_ratios() -> None:
    with pytest.raises(ValueError, match="back_width_ratio must be smaller"):
        create_virtual_piano_keys(
            frame_width=100,
            frame_height=100,
            back_width_ratio=1.0,
            front_width_ratio=0.7,
        )


def test_piano_key_center_returns_average_point() -> None:
    key = create_virtual_piano_keys(
        frame_width=100,
        frame_height=100,
        notes=("C",),
        top_y_ratio=0.5,
        bottom_y_ratio=0.9,
        back_width_ratio=0.6,
        front_width_ratio=1.0,
    )[0]

    assert key.center == PianoPoint(x=50, y=70)


def test_is_point_on_segment_returns_true_for_point_on_segment() -> None:
    result = is_point_on_segment(
        point=PianoPoint(x=5, y=5),
        segment_start=PianoPoint(x=0, y=0),
        segment_end=PianoPoint(x=10, y=10),
    )

    assert result


def test_is_point_on_segment_returns_false_for_point_outside_segment() -> None:
    result = is_point_on_segment(
        point=PianoPoint(x=15, y=15),
        segment_start=PianoPoint(x=0, y=0),
        segment_end=PianoPoint(x=10, y=10),
    )

    assert not result


def test_is_point_inside_polygon_returns_true_for_inside_point() -> None:
    polygon = (
        PianoPoint(x=0, y=0),
        PianoPoint(x=10, y=0),
        PianoPoint(x=10, y=10),
        PianoPoint(x=0, y=10),
    )

    assert is_point_inside_polygon(point=PianoPoint(x=5, y=5), polygon=polygon)


def test_is_point_inside_polygon_returns_true_for_boundary_point() -> None:
    polygon = (
        PianoPoint(x=0, y=0),
        PianoPoint(x=10, y=0),
        PianoPoint(x=10, y=10),
        PianoPoint(x=0, y=10),
    )

    assert is_point_inside_polygon(point=PianoPoint(x=0, y=5), polygon=polygon)


def test_is_point_inside_polygon_returns_false_for_outside_point() -> None:
    polygon = (
        PianoPoint(x=0, y=0),
        PianoPoint(x=10, y=0),
        PianoPoint(x=10, y=10),
        PianoPoint(x=0, y=10),
    )

    assert not is_point_inside_polygon(point=PianoPoint(x=20, y=5), polygon=polygon)


def test_is_point_inside_polygon_rejects_invalid_polygon() -> None:
    with pytest.raises(ValueError, match="polygon must contain"):
        is_point_inside_polygon(
            point=PianoPoint(x=0, y=0),
            polygon=(PianoPoint(x=0, y=0), PianoPoint(x=1, y=1)),
        )


def test_is_point_inside_key_returns_true_for_point_inside_key() -> None:
    key = create_virtual_piano_keys(
        frame_width=100,
        frame_height=100,
        notes=("C",),
    )[0]

    assert is_point_inside_key(point=key.center, key=key)


def test_find_hovered_key_returns_key_under_fingertip() -> None:
    keys = create_virtual_piano_keys(
        frame_width=100,
        frame_height=100,
        notes=("C", "D"),
        top_y_ratio=0.5,
        bottom_y_ratio=0.9,
        back_width_ratio=1.0,
        front_width_ratio=1.0,
    )
    fingertip = Fingertip(x=75, y=70)

    hovered_key = find_hovered_key(fingertip=fingertip, keys=keys)

    assert hovered_key is not None
    assert hovered_key.note == "D"


def test_find_hovered_key_returns_none_outside_keys() -> None:
    keys = create_virtual_piano_keys(frame_width=100, frame_height=100)
    fingertip = Fingertip(x=50, y=10)

    assert find_hovered_key(fingertip=fingertip, keys=keys) is None


def test_get_pressed_key_indexes_returns_unique_key_indexes() -> None:
    keys = create_virtual_piano_keys(
        frame_width=100,
        frame_height=100,
        notes=("C", "D"),
        top_y_ratio=0.5,
        bottom_y_ratio=0.9,
        back_width_ratio=1.0,
        front_width_ratio=1.0,
    )
    fingertips = [
        Fingertip(x=25, y=70, label="index"),
        Fingertip(x=25, y=75, label="middle"),
        Fingertip(x=75, y=70, label="ring"),
    ]

    pressed_key_indexes = get_pressed_key_indexes(
        fingertips=fingertips,
        keys=keys,
    )

    assert pressed_key_indexes == frozenset({0, 1})


def test_create_piano_triggers_returns_newly_pressed_keys_only() -> None:
    keys = create_virtual_piano_keys(
        frame_width=100,
        frame_height=100,
        notes=("C", "D", "E"),
    )
    previous_state = PianoState(pressed_key_indexes=frozenset({0}))

    triggers = create_piano_triggers(
        previous_state=previous_state,
        current_pressed_key_indexes=frozenset({0, 2}),
        keys=keys,
        current_time=10.0,
    )

    assert len(triggers) == 1
    assert triggers[0].key_index == 2
    assert triggers[0].note == "E"
    assert triggers[0].triggered_at == 10.0


def test_create_piano_triggers_skips_unknown_key_indexes() -> None:
    keys = create_virtual_piano_keys(
        frame_width=100,
        frame_height=100,
        notes=("C",),
    )

    triggers = create_piano_triggers(
        previous_state=PianoState(),
        current_pressed_key_indexes=frozenset({99}),
        keys=keys,
        current_time=10.0,
    )

    assert triggers == []


def test_update_piano_state_updates_pressed_keys_and_last_note() -> None:
    keys = create_virtual_piano_keys(
        frame_width=100,
        frame_height=100,
        notes=("C", "D"),
    )
    triggers = create_piano_triggers(
        previous_state=PianoState(),
        current_pressed_key_indexes=frozenset({1}),
        keys=keys,
        current_time=10.0,
    )

    state = update_piano_state(
        previous_state=PianoState(),
        current_pressed_key_indexes=frozenset({1}),
        triggers=triggers,
    )

    assert state.pressed_key_indexes == frozenset({1})
    assert state.total_triggers == 1
    assert state.last_note == "D"


def test_update_piano_state_preserves_last_note_without_triggers() -> None:
    previous_state = PianoState(
        pressed_key_indexes=frozenset({0}),
        total_triggers=1,
        last_note="C",
    )

    state = update_piano_state(
        previous_state=previous_state,
        current_pressed_key_indexes=frozenset(),
        triggers=[],
    )

    assert state.pressed_key_indexes == frozenset()
    assert state.total_triggers == 1
    assert state.last_note == "C"


def test_get_piano_message_returns_pressed_notes() -> None:
    keys = create_virtual_piano_keys(
        frame_width=100,
        frame_height=100,
        notes=("C",),
    )
    triggers = create_piano_triggers(
        previous_state=PianoState(),
        current_pressed_key_indexes=frozenset({0}),
        keys=keys,
        current_time=10.0,
    )

    message = get_piano_message(
        triggers=triggers,
        state=PianoState(),
    )

    assert message == "Pressed: C"


def test_get_piano_message_returns_last_note() -> None:
    message = get_piano_message(
        triggers=[],
        state=PianoState(last_note="D"),
    )

    assert message == "Last note: D"


def test_get_piano_message_returns_instruction() -> None:
    message = get_piano_message(
        triggers=[],
        state=PianoState(),
    )

    assert "Move your index finger" in message
