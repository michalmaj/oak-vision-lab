import numpy as np
import pytest

from oak_vision_lab.demos.virtual_depth_piano import (
    DisparityRoi,
    Fingertip,
    FingertipDepthSample,
    NormalizedLandmark,
    PianoPoint,
    PianoState,
    compute_roi_mean_disparity,
    create_disparity_roi_around_point,
    create_note_waveform,
    create_piano_triggers,
    create_virtual_piano_keys,
    extract_fingertips_from_mediapipe_results,
    extract_fingertips_from_normalized_landmarks,
    extract_normalized_landmarks_from_mediapipe_hand,
    find_hovered_key,
    get_depth_pressed_key_indexes,
    get_note_frequency,
    get_piano_message,
    get_pressed_key_indexes,
    is_depth_press,
    is_point_inside_key,
    is_point_inside_polygon,
    is_point_on_segment,
    maybe_mirror_frame,
    measure_fingertip_depth,
    measure_fingertips_depth,
    scale_fingertip_to_frame,
    scale_normalized_landmark,
    update_piano_state,
)


class FakeMediaPipeTasksResults:
    def __init__(self, hand_landmarks) -> None:
        self.hand_landmarks = hand_landmarks


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


class FakeMediaPipeLandmark:
    def __init__(self, *, x: float, y: float) -> None:
        self.x = x
        self.y = y


class FakeMediaPipeHandLandmarks:
    def __init__(self, landmarks: list[FakeMediaPipeLandmark]) -> None:
        self.landmark = landmarks


class FakeMediaPipeResults:
    def __init__(self, multi_hand_landmarks) -> None:
        self.multi_hand_landmarks = multi_hand_landmarks


def test_scale_normalized_landmark_scales_to_image_coordinates() -> None:
    fingertip = scale_normalized_landmark(
        landmark=NormalizedLandmark(x=0.5, y=0.25),
        frame_width=101,
        frame_height=81,
        label="index",
    )

    assert fingertip == Fingertip(x=50, y=20, label="index")


def test_scale_normalized_landmark_clamps_to_frame_bounds() -> None:
    fingertip = scale_normalized_landmark(
        landmark=NormalizedLandmark(x=2.0, y=-1.0),
        frame_width=100,
        frame_height=80,
        label="index",
    )

    assert fingertip == Fingertip(x=99, y=0, label="index")


def test_scale_normalized_landmark_rejects_invalid_frame_dimensions() -> None:
    with pytest.raises(ValueError, match="frame dimensions must be positive"):
        scale_normalized_landmark(
            landmark=NormalizedLandmark(x=0.5, y=0.5),
            frame_width=0,
            frame_height=80,
            label="index",
        )


def test_extract_fingertips_from_normalized_landmarks_extracts_selected_points() -> (
    None
):
    landmarks = [NormalizedLandmark(x=0.0, y=0.0) for _ in range(21)]
    landmarks[8] = NormalizedLandmark(x=0.5, y=0.25)
    landmarks[12] = NormalizedLandmark(x=0.75, y=0.5)

    fingertips = extract_fingertips_from_normalized_landmarks(
        landmarks=landmarks,
        frame_width=101,
        frame_height=81,
        fingertip_landmarks={
            "index": 8,
            "middle": 12,
        },
    )

    assert fingertips == [
        Fingertip(x=50, y=20, label="index"),
        Fingertip(x=75, y=40, label="middle"),
    ]


def test_extract_fingertips_from_normalized_landmarks_skips_missing_indexes() -> None:
    landmarks = [NormalizedLandmark(x=0.0, y=0.0) for _ in range(5)]

    fingertips = extract_fingertips_from_normalized_landmarks(
        landmarks=landmarks,
        frame_width=100,
        frame_height=80,
        fingertip_landmarks={"index": 8},
    )

    assert fingertips == []


def test_extract_normalized_landmarks_from_mediapipe_hand_converts_landmarks() -> None:
    hand_landmarks = FakeMediaPipeHandLandmarks(
        [
            FakeMediaPipeLandmark(x=0.1, y=0.2),
            FakeMediaPipeLandmark(x=0.3, y=0.4),
        ],
    )

    landmarks = extract_normalized_landmarks_from_mediapipe_hand(hand_landmarks)

    assert landmarks == [
        NormalizedLandmark(x=0.1, y=0.2),
        NormalizedLandmark(x=0.3, y=0.4),
    ]


def test_extract_fingertips_from_mediapipe_results_returns_empty_without_hands() -> (
    None
):
    results = FakeMediaPipeResults(multi_hand_landmarks=None)

    fingertips = extract_fingertips_from_mediapipe_results(
        results=results,
        frame_width=100,
        frame_height=80,
    )

    assert fingertips == []


def test_extract_fingertips_from_mediapipe_results_extracts_from_multiple_hands() -> (
    None
):
    first_hand = FakeMediaPipeHandLandmarks(
        [FakeMediaPipeLandmark(x=0.0, y=0.0) for _ in range(21)],
    )
    second_hand = FakeMediaPipeHandLandmarks(
        [FakeMediaPipeLandmark(x=0.0, y=0.0) for _ in range(21)],
    )
    first_hand.landmark[8] = FakeMediaPipeLandmark(x=0.5, y=0.25)
    second_hand.landmark[8] = FakeMediaPipeLandmark(x=0.75, y=0.5)

    results = FakeMediaPipeResults(
        multi_hand_landmarks=[
            first_hand,
            second_hand,
        ],
    )

    fingertips = extract_fingertips_from_mediapipe_results(
        results=results,
        frame_width=101,
        frame_height=81,
    )

    assert fingertips == [
        Fingertip(x=50, y=20, label="index"),
        Fingertip(x=75, y=40, label="index"),
    ]


def test_extract_fingertips_from_mediapipe_tasks_results_extracts_hands() -> None:
    hand_landmarks = [FakeMediaPipeLandmark(x=0.0, y=0.0) for _ in range(21)]
    hand_landmarks[8] = FakeMediaPipeLandmark(x=0.5, y=0.25)

    results = FakeMediaPipeTasksResults(
        hand_landmarks=[
            hand_landmarks,
        ],
    )

    fingertips = extract_fingertips_from_mediapipe_results(
        results=results,
        frame_width=101,
        frame_height=81,
    )

    assert fingertips == [
        Fingertip(x=50, y=20, label="index"),
    ]


def test_scale_fingertip_to_frame_scales_coordinates() -> None:
    point = scale_fingertip_to_frame(
        fingertip=Fingertip(x=50, y=20, label="index"),
        source_width=100,
        source_height=80,
        target_width=200,
        target_height=160,
    )

    assert point == PianoPoint(x=100, y=40)


def test_scale_fingertip_to_frame_clamps_coordinates() -> None:
    point = scale_fingertip_to_frame(
        fingertip=Fingertip(x=150, y=-10, label="index"),
        source_width=100,
        source_height=80,
        target_width=200,
        target_height=160,
    )

    assert point == PianoPoint(x=199, y=0)


def test_scale_fingertip_to_frame_rejects_invalid_source_dimensions() -> None:
    with pytest.raises(ValueError, match="source dimensions must be positive"):
        scale_fingertip_to_frame(
            fingertip=Fingertip(x=10, y=10),
            source_width=0,
            source_height=80,
            target_width=200,
            target_height=160,
        )


def test_scale_fingertip_to_frame_rejects_invalid_target_dimensions() -> None:
    with pytest.raises(ValueError, match="target dimensions must be positive"):
        scale_fingertip_to_frame(
            fingertip=Fingertip(x=10, y=10),
            source_width=100,
            source_height=80,
            target_width=0,
            target_height=160,
        )


def test_create_disparity_roi_around_point_returns_clipped_roi() -> None:
    roi = create_disparity_roi_around_point(
        point=PianoPoint(x=2, y=3),
        frame_width=20,
        frame_height=20,
        radius=5,
    )

    assert roi == DisparityRoi(x=0, y=0, width=8, height=9)


def test_create_disparity_roi_around_point_rejects_invalid_frame_dimensions() -> None:
    with pytest.raises(ValueError, match="frame dimensions must be positive"):
        create_disparity_roi_around_point(
            point=PianoPoint(x=2, y=3),
            frame_width=0,
            frame_height=20,
        )


def test_create_disparity_roi_around_point_rejects_negative_radius() -> None:
    with pytest.raises(ValueError, match="radius must be non-negative"):
        create_disparity_roi_around_point(
            point=PianoPoint(x=2, y=3),
            frame_width=20,
            frame_height=20,
            radius=-1,
        )


def test_compute_roi_mean_disparity_ignores_zero_values() -> None:
    frame = np.array(
        [
            [0, 0, 0, 0],
            [0, 10, 20, 0],
            [0, 30, 40, 0],
            [0, 0, 0, 0],
        ],
        dtype=np.uint8,
    )
    roi = DisparityRoi(x=1, y=1, width=2, height=2)

    result = compute_roi_mean_disparity(
        disparity_frame=frame,
        roi=roi,
    )

    assert result == 25.0


def test_compute_roi_mean_disparity_returns_zero_without_valid_pixels() -> None:
    frame = np.zeros((4, 4), dtype=np.uint8)
    roi = DisparityRoi(x=1, y=1, width=2, height=2)

    result = compute_roi_mean_disparity(
        disparity_frame=frame,
        roi=roi,
    )

    assert result == 0.0


def test_is_depth_press_returns_true_above_threshold() -> None:
    assert is_depth_press(mean_disparity=30.0, press_disparity_threshold=25.0)


def test_is_depth_press_returns_false_below_threshold() -> None:
    assert not is_depth_press(mean_disparity=20.0, press_disparity_threshold=25.0)


def test_is_depth_press_rejects_negative_threshold() -> None:
    with pytest.raises(ValueError, match="press_disparity_threshold must be"):
        is_depth_press(mean_disparity=20.0, press_disparity_threshold=-1.0)


def test_measure_fingertip_depth_returns_pressed_sample() -> None:
    disparity_frame = np.ones((80, 100), dtype=np.uint8) * 40

    sample = measure_fingertip_depth(
        fingertip=Fingertip(x=50, y=40, label="index"),
        rgb_width=100,
        rgb_height=80,
        disparity_frame=disparity_frame,
        roi_radius=2,
        press_disparity_threshold=25.0,
    )

    assert sample.fingertip == Fingertip(x=50, y=40, label="index")
    assert sample.disparity_point == PianoPoint(x=50, y=40)
    assert sample.mean_disparity == 40.0
    assert sample.pressed


def test_measure_fingertips_depth_returns_samples_for_all_fingertips() -> None:
    disparity_frame = np.ones((80, 100), dtype=np.uint8) * 40

    samples = measure_fingertips_depth(
        fingertips=[
            Fingertip(x=10, y=10, label="index"),
            Fingertip(x=20, y=20, label="middle"),
        ],
        rgb_width=100,
        rgb_height=80,
        disparity_frame=disparity_frame,
        roi_radius=2,
        press_disparity_threshold=25.0,
    )

    assert len(samples) == 2
    assert all(sample.pressed for sample in samples)


def test_get_depth_pressed_key_indexes_returns_only_depth_pressed_keys() -> None:
    keys = create_virtual_piano_keys(
        frame_width=100,
        frame_height=100,
        notes=("C", "D"),
        top_y_ratio=0.5,
        bottom_y_ratio=0.9,
        back_width_ratio=1.0,
        front_width_ratio=1.0,
    )
    samples = [
        FingertipDepthSample(
            fingertip=Fingertip(x=25, y=70, label="index"),
            disparity_point=PianoPoint(x=25, y=70),
            roi=DisparityRoi(x=20, y=65, width=10, height=10),
            mean_disparity=40.0,
            pressed=True,
        ),
        FingertipDepthSample(
            fingertip=Fingertip(x=75, y=70, label="middle"),
            disparity_point=PianoPoint(x=75, y=70),
            roi=DisparityRoi(x=70, y=65, width=10, height=10),
            mean_disparity=10.0,
            pressed=False,
        ),
    ]

    pressed_key_indexes = get_depth_pressed_key_indexes(
        depth_samples=samples,
        keys=keys,
    )

    assert pressed_key_indexes == frozenset({0})


def test_get_note_frequency_returns_frequency_for_supported_note() -> None:
    assert get_note_frequency("A") == 440.0


def test_get_note_frequency_rejects_unsupported_note() -> None:
    with pytest.raises(ValueError, match="unsupported note"):
        get_note_frequency("H")


def test_create_note_waveform_returns_int16_samples() -> None:
    waveform = create_note_waveform(
        frequency=440.0,
        duration_seconds=0.1,
        sample_rate=1000,
        volume=0.5,
    )

    assert waveform.dtype == np.int16
    assert waveform.shape == (100,)


def test_create_note_waveform_rejects_invalid_frequency() -> None:
    with pytest.raises(ValueError, match="frequency must be positive"):
        create_note_waveform(frequency=0.0)


def test_create_note_waveform_rejects_invalid_duration() -> None:
    with pytest.raises(ValueError, match="duration_seconds must be positive"):
        create_note_waveform(frequency=440.0, duration_seconds=0.0)


def test_create_note_waveform_rejects_invalid_sample_rate() -> None:
    with pytest.raises(ValueError, match="sample_rate must be positive"):
        create_note_waveform(frequency=440.0, sample_rate=0)


def test_create_note_waveform_rejects_invalid_volume() -> None:
    with pytest.raises(ValueError, match="volume must be between"):
        create_note_waveform(frequency=440.0, volume=2.0)


def test_maybe_mirror_frame_returns_same_frame_when_disabled() -> None:
    frame = np.array(
        [
            [1, 2, 3],
            [4, 5, 6],
        ],
        dtype=np.uint8,
    )

    result = maybe_mirror_frame(frame, mirror=False)

    assert np.array_equal(result, frame)


def test_maybe_mirror_frame_flips_frame_when_enabled() -> None:
    frame = np.array(
        [
            [1, 2, 3],
            [4, 5, 6],
        ],
        dtype=np.uint8,
    )

    result = maybe_mirror_frame(frame, mirror=True)

    expected = np.array(
        [
            [3, 2, 1],
            [6, 5, 4],
        ],
        dtype=np.uint8,
    )

    assert np.array_equal(result, expected)
