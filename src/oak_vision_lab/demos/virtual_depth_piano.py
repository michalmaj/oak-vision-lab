"""Virtual depth piano geometry and interaction logic."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

import cv2
import depthai as dai
import numpy as np

from oak_vision_lab.depth.disparity import colorize_disparity_frame

DEFAULT_NOTES = ("C", "D", "E", "F", "G", "A", "B", "C5")

BLACK_KEY_NOTE_BY_WHITE_PAIR = {
    ("C", "D"): "C#",
    ("D", "E"): "D#",
    ("F", "G"): "F#",
    ("G", "A"): "G#",
    ("A", "B"): "A#",
}

BLACK_KEY_HEIGHT_RATIO = 0.58
BLACK_KEY_TOP_WIDTH_RATIO = 0.52
BLACK_KEY_BOTTOM_WIDTH_RATIO = 0.46

NOTE_FREQUENCIES = {
    "C": 261.63,
    "C#": 277.18,
    "D": 293.66,
    "D#": 311.13,
    "E": 329.63,
    "F": 349.23,
    "F#": 369.99,
    "G": 392.00,
    "G#": 415.30,
    "A": 440.00,
    "A#": 466.16,
    "B": 493.88,
    "C5": 523.25,
}

DEFAULT_AUDIO_NOTES = tuple(NOTE_FREQUENCIES)

AUDIO_SAMPLE_RATE = 44_100
AUDIO_DURATION_SECONDS = 0.18
AUDIO_VOLUME = 0.35

DEFAULT_TOP_Y_RATIO = 0.52
DEFAULT_BOTTOM_Y_RATIO = 0.92
DEFAULT_BACK_WIDTH_RATIO = 0.68
DEFAULT_FRONT_WIDTH_RATIO = 0.96

WINDOW_NAME = "oak-vision-lab | Virtual Depth Piano"

RGB_STREAM_NAME = "rgb"
DISPARITY_STREAM_NAME = "disparity"

MIRROR_VIEW = True

RGB_PREVIEW_WIDTH = 640
RGB_PREVIEW_HEIGHT = 400

MEDIAPIPE_MAX_NUM_HANDS = 2
MEDIAPIPE_MIN_DETECTION_CONFIDENCE = 0.6
MEDIAPIPE_MIN_TRACKING_CONFIDENCE = 0.5

DEFAULT_PRESS_DISPARITY_THRESHOLD = (
    25.0  # Lower if it's too hard to press, if it's too easy, set value a big higher
)
DEFAULT_FINGERTIP_ROI_RADIUS = 10

INDEX_FINGER_TIP_LANDMARK = 8
MIDDLE_FINGER_TIP_LANDMARK = 12
RING_FINGER_TIP_LANDMARK = 16
PINKY_TIP_LANDMARK = 20

DEFAULT_FINGERTIP_LANDMARKS = {
    "index": INDEX_FINGER_TIP_LANDMARK,
}

DEFAULT_HAND_LANDMARKER_MODEL_PATH = Path(
    "models/mediapipe/hand_landmarker.task",
)


class PianoKeyKind(Enum):
    """Virtual piano key type."""

    WHITE = "white"
    BLACK = "black"


@dataclass(frozen=True)
class PianoPoint:
    """2D point used by virtual piano geometry."""

    x: int
    y: int


@dataclass(frozen=True)
class PianoKey:
    """Pseudo-3D virtual piano key represented as a quadrilateral."""

    index: int
    note: str
    points: tuple[PianoPoint, PianoPoint, PianoPoint, PianoPoint]
    kind: PianoKeyKind = PianoKeyKind.WHITE

    @property
    def center(self) -> PianoPoint:
        """Return approximate key center."""

        x = round(sum(point.x for point in self.points) / len(self.points))
        y = round(sum(point.y for point in self.points) / len(self.points))

        return PianoPoint(x=x, y=y)


@dataclass(frozen=True)
class Fingertip:
    """Detected fingertip position in image coordinates."""

    x: int
    y: int
    label: str = "index"


@dataclass(frozen=True)
class DisparityRoi:
    """Small disparity region used for fingertip depth measurement."""

    x: int
    y: int
    width: int
    height: int

    @property
    def x2(self) -> int:
        """Return the right edge coordinate."""

        return self.x + self.width

    @property
    def y2(self) -> int:
        """Return the bottom edge coordinate."""

        return self.y + self.height


@dataclass(frozen=True)
class FingertipDepthSample:
    """Depth measurement associated with a fingertip."""

    fingertip: Fingertip
    disparity_point: PianoPoint
    roi: DisparityRoi
    mean_disparity: float
    pressed: bool


@dataclass(frozen=True)
class NormalizedLandmark:
    """Normalized landmark coordinates returned by hand tracking."""

    x: float
    y: float


@dataclass(frozen=True)
class PianoTrigger:
    """Triggered piano note event."""

    key_index: int
    note: str
    triggered_at: float


@dataclass(frozen=True)
class PianoState:
    """Virtual piano interaction state."""

    pressed_key_indexes: frozenset[int] = frozenset()
    total_triggers: int = 0
    last_note: str | None = None


class NoteAudioPlayer:
    """Small pygame-based note player for the virtual depth piano."""

    def __init__(
        self,
        *,
        sample_rate: int = AUDIO_SAMPLE_RATE,
        duration_seconds: float = AUDIO_DURATION_SECONDS,
        volume: float = AUDIO_VOLUME,
    ) -> None:
        self.sample_rate = sample_rate
        self.duration_seconds = duration_seconds
        self.volume = volume
        self.enabled = False
        self.status_message = "Audio: OFF"
        self._pygame: Any | None = None
        self._sounds: dict[str, Any] = {}

    def initialize(self, *, notes: tuple[str, ...] = DEFAULT_AUDIO_NOTES) -> None:
        """Initialize pygame mixer and prepare note sounds."""

        try:
            import pygame

            pygame.mixer.init(
                frequency=self.sample_rate,
                size=-16,
                channels=1,
                buffer=512,
            )
            pygame.mixer.set_num_channels(16)

            self._pygame = pygame
            self._sounds = {
                note: pygame.sndarray.make_sound(
                    create_note_waveform(
                        frequency=get_note_frequency(note),
                        duration_seconds=self.duration_seconds,
                        sample_rate=self.sample_rate,
                        volume=self.volume,
                    ),
                )
                for note in notes
            }

            self.enabled = True
            self.status_message = "Audio: ON"
        except Exception as error:
            self.enabled = False
            self.status_message = f"Audio unavailable: {error}"

    def play_note(self, note: str) -> None:
        """Play a note if audio is available."""

        if not self.enabled:
            return

        sound = self._sounds.get(note)

        if sound is None:
            return

        sound.play()

    def play_triggers(self, triggers: list[PianoTrigger]) -> None:
        """Play all triggered notes."""

        for trigger in triggers:
            self.play_note(trigger.note)

    def shutdown(self) -> None:
        """Shutdown pygame mixer if it was initialized."""

        if self._pygame is None:
            return

        if self._pygame.mixer.get_init():
            self._pygame.mixer.quit()


def create_rgb_disparity_pipeline() -> tuple[dai.Pipeline, float]:
    """Create an OAK-D pipeline with RGB preview and stereo disparity output."""

    pipeline = dai.Pipeline()

    color_camera = pipeline.create(dai.node.ColorCamera)
    mono_left = pipeline.create(dai.node.MonoCamera)
    mono_right = pipeline.create(dai.node.MonoCamera)
    stereo = pipeline.create(dai.node.StereoDepth)

    rgb_output = pipeline.create(dai.node.XLinkOut)
    disparity_output = pipeline.create(dai.node.XLinkOut)

    rgb_output.setStreamName(RGB_STREAM_NAME)
    disparity_output.setStreamName(DISPARITY_STREAM_NAME)

    color_camera.setBoardSocket(dai.CameraBoardSocket.RGB)
    color_camera.setPreviewSize(RGB_PREVIEW_WIDTH, RGB_PREVIEW_HEIGHT)
    color_camera.setInterleaved(False)
    color_camera.setColorOrder(dai.ColorCameraProperties.ColorOrder.BGR)

    mono_left.setBoardSocket(dai.CameraBoardSocket.LEFT)
    mono_right.setBoardSocket(dai.CameraBoardSocket.RIGHT)
    mono_left.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)
    mono_right.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)

    stereo.setDefaultProfilePreset(dai.node.StereoDepth.PresetMode.HIGH_DENSITY)
    stereo.setLeftRightCheck(True)
    stereo.setSubpixel(False)

    mono_left.out.link(stereo.left)
    mono_right.out.link(stereo.right)

    color_camera.preview.link(rgb_output.input)
    stereo.disparity.link(disparity_output.input)

    max_disparity = float(stereo.initialConfig.getMaxDisparity())

    return pipeline, max_disparity


def create_hand_tracker(
    *,
    model_path: Path = DEFAULT_HAND_LANDMARKER_MODEL_PATH,
) -> Any:
    """Create a MediaPipe Tasks hand landmarker."""

    if not model_path.exists():
        msg = (
            "MediaPipe hand landmarker model was not found. "
            f"Expected path: {model_path}. "
            "Download hand_landmarker.task and place it there."
        )
        raise FileNotFoundError(msg)

    import mediapipe as mp

    BaseOptions = mp.tasks.BaseOptions
    HandLandmarker = mp.tasks.vision.HandLandmarker
    HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
    VisionRunningMode = mp.tasks.vision.RunningMode

    options = HandLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=str(model_path)),
        running_mode=VisionRunningMode.VIDEO,
        num_hands=MEDIAPIPE_MAX_NUM_HANDS,
        min_hand_detection_confidence=MEDIAPIPE_MIN_DETECTION_CONFIDENCE,
        min_tracking_confidence=MEDIAPIPE_MIN_TRACKING_CONFIDENCE,
    )

    return HandLandmarker.create_from_options(options)


def validate_ratio(
    *,
    value: float,
    name: str,
) -> None:
    """Validate a normalized ratio."""

    if not 0.0 < value <= 1.0:
        msg = f"{name} must be in the range (0.0, 1.0]"
        raise ValueError(msg)


def create_virtual_piano_keys(
    *,
    frame_width: int,
    frame_height: int,
    notes: tuple[str, ...] = DEFAULT_NOTES,
    top_y_ratio: float = DEFAULT_TOP_Y_RATIO,
    bottom_y_ratio: float = DEFAULT_BOTTOM_Y_RATIO,
    back_width_ratio: float = DEFAULT_BACK_WIDTH_RATIO,
    front_width_ratio: float = DEFAULT_FRONT_WIDTH_RATIO,
) -> list[PianoKey]:
    """Create pseudo-3D piano keys as perspective quadrilaterals."""

    if frame_width <= 0 or frame_height <= 0:
        msg = "frame dimensions must be positive"
        raise ValueError(msg)

    if not notes:
        msg = "notes must not be empty"
        raise ValueError(msg)

    validate_ratio(value=top_y_ratio, name="top_y_ratio")
    validate_ratio(value=bottom_y_ratio, name="bottom_y_ratio")
    validate_ratio(value=back_width_ratio, name="back_width_ratio")
    validate_ratio(value=front_width_ratio, name="front_width_ratio")

    if top_y_ratio >= bottom_y_ratio:
        msg = "top_y_ratio must be smaller than bottom_y_ratio"
        raise ValueError(msg)

    if back_width_ratio > front_width_ratio:
        msg = "back_width_ratio must be smaller than or equal to front_width_ratio"
        raise ValueError(msg)

    top_y = round(frame_height * top_y_ratio)
    bottom_y = round(frame_height * bottom_y_ratio)

    back_width = round(frame_width * back_width_ratio)
    front_width = round(frame_width * front_width_ratio)

    back_x = round((frame_width - back_width) / 2)
    front_x = round((frame_width - front_width) / 2)

    key_count = len(notes)
    keys: list[PianoKey] = []

    for index, note in enumerate(notes):
        back_left = round(back_x + index * back_width / key_count)
        back_right = round(back_x + (index + 1) * back_width / key_count)
        front_left = round(front_x + index * front_width / key_count)
        front_right = round(front_x + (index + 1) * front_width / key_count)

        keys.append(
            PianoKey(
                index=index,
                note=note,
                points=(
                    PianoPoint(x=back_left, y=top_y),
                    PianoPoint(x=back_right, y=top_y),
                    PianoPoint(x=front_right, y=bottom_y),
                    PianoPoint(x=front_left, y=bottom_y),
                ),
                kind=PianoKeyKind.WHITE,
            ),
        )

    return keys


def get_note_base(note: str) -> str:
    """Return note name without octave suffix."""

    return "".join(character for character in note if not character.isdigit())


def get_black_key_note_between(
    *,
    left_note: str,
    right_note: str,
) -> str | None:
    """Return black key note between two white notes, if it exists."""

    left_base = get_note_base(left_note)
    right_base = get_note_base(right_note)

    return BLACK_KEY_NOTE_BY_WHITE_PAIR.get((left_base, right_base))


def interpolate_x_at_y(
    *,
    start: PianoPoint,
    end: PianoPoint,
    y: int,
) -> int:
    """Interpolate x coordinate on a line segment for the given y coordinate."""

    if start.y == end.y:
        return round((start.x + end.x) / 2)

    ratio = (y - start.y) / (end.y - start.y)

    return round(start.x + ratio * (end.x - start.x))


def create_black_piano_keys(
    *,
    white_keys: list[PianoKey],
    start_index: int | None = None,
    height_ratio: float = BLACK_KEY_HEIGHT_RATIO,
    top_width_ratio: float = BLACK_KEY_TOP_WIDTH_RATIO,
    bottom_width_ratio: float = BLACK_KEY_BOTTOM_WIDTH_RATIO,
) -> list[PianoKey]:
    """Create pseudo-3D black keys between compatible white keys."""

    if not white_keys:
        return []

    validate_ratio(value=height_ratio, name="height_ratio")
    validate_ratio(value=top_width_ratio, name="top_width_ratio")
    validate_ratio(value=bottom_width_ratio, name="bottom_width_ratio")

    next_index = start_index
    if next_index is None:
        next_index = max(key.index for key in white_keys) + 1

    black_keys: list[PianoKey] = []

    for left_key, right_key in zip(white_keys, white_keys[1:], strict=False):
        black_note = get_black_key_note_between(
            left_note=left_key.note,
            right_note=right_key.note,
        )

        if black_note is None:
            continue

        top_left = left_key.points[1]
        bottom_left = left_key.points[2]

        white_top_width = max(1, left_key.points[1].x - left_key.points[0].x)
        white_bottom_width = max(1, left_key.points[2].x - left_key.points[3].x)

        top_width = max(6, round(white_top_width * top_width_ratio))
        bottom_width = max(8, round(white_bottom_width * bottom_width_ratio))

        black_top_y = top_left.y
        black_bottom_y = round(
            black_top_y + (left_key.points[2].y - black_top_y) * height_ratio,
        )

        boundary_top_x = top_left.x
        boundary_bottom_x = interpolate_x_at_y(
            start=top_left,
            end=bottom_left,
            y=black_bottom_y,
        )

        black_keys.append(
            PianoKey(
                index=next_index,
                note=black_note,
                points=(
                    PianoPoint(
                        x=boundary_top_x - top_width // 2,
                        y=black_top_y,
                    ),
                    PianoPoint(
                        x=boundary_top_x + top_width // 2,
                        y=black_top_y,
                    ),
                    PianoPoint(
                        x=boundary_bottom_x + bottom_width // 2,
                        y=black_bottom_y,
                    ),
                    PianoPoint(
                        x=boundary_bottom_x - bottom_width // 2,
                        y=black_bottom_y,
                    ),
                ),
                kind=PianoKeyKind.BLACK,
            ),
        )
        next_index += 1

    return black_keys


def create_virtual_piano_keyboard(
    *,
    frame_width: int,
    frame_height: int,
    notes: tuple[str, ...] = DEFAULT_NOTES,
) -> list[PianoKey]:
    """Create full virtual piano keyboard with white and black keys."""

    white_keys = create_virtual_piano_keys(
        frame_width=frame_width,
        frame_height=frame_height,
        notes=notes,
    )
    black_keys = create_black_piano_keys(
        white_keys=white_keys,
    )

    return [*white_keys, *black_keys]


def sort_keys_for_hit_testing(keys: list[PianoKey]) -> list[PianoKey]:
    """Return keys ordered so visually topmost keys are tested first."""

    return sorted(
        keys,
        key=lambda key: 0 if key.kind == PianoKeyKind.BLACK else 1,
    )


def scale_normalized_landmark(
    *,
    landmark: NormalizedLandmark,
    frame_width: int,
    frame_height: int,
    label: str,
) -> Fingertip:
    """Scale a normalized landmark to image coordinates."""

    if frame_width <= 0 or frame_height <= 0:
        msg = "frame dimensions must be positive"
        raise ValueError(msg)

    x = round(landmark.x * (frame_width - 1))
    y = round(landmark.y * (frame_height - 1))

    x = max(0, min(frame_width - 1, x))
    y = max(0, min(frame_height - 1, y))

    return Fingertip(x=x, y=y, label=label)


def extract_fingertips_from_normalized_landmarks(
    *,
    landmarks: list[NormalizedLandmark],
    frame_width: int,
    frame_height: int,
    fingertip_landmarks: dict[str, int] | None = None,
) -> list[Fingertip]:
    """Extract selected fingertips from normalized hand landmarks."""

    selected_landmarks = fingertip_landmarks or DEFAULT_FINGERTIP_LANDMARKS
    fingertips: list[Fingertip] = []

    for label, landmark_index in selected_landmarks.items():
        if landmark_index >= len(landmarks):
            continue

        fingertips.append(
            scale_normalized_landmark(
                landmark=landmarks[landmark_index],
                frame_width=frame_width,
                frame_height=frame_height,
                label=label,
            ),
        )

    return fingertips


def extract_normalized_landmarks_from_mediapipe_hand(
    hand_landmarks: Any,
) -> list[NormalizedLandmark]:
    """Convert MediaPipe hand landmarks to internal normalized landmarks."""

    return [
        NormalizedLandmark(
            x=float(landmark.x),
            y=float(landmark.y),
        )
        for landmark in hand_landmarks.landmark
    ]


def extract_fingertips_from_mediapipe_results(
    *,
    results: Any,
    frame_width: int,
    frame_height: int,
    fingertip_landmarks: dict[str, int] | None = None,
) -> list[Fingertip]:
    """Extract fingertips from MediaPipe hand tracking results."""

    tasks_hand_landmarks = getattr(results, "hand_landmarks", None)

    if tasks_hand_landmarks:
        fingertips: list[Fingertip] = []

        for hand_landmarks in tasks_hand_landmarks:
            normalized_landmarks = [
                NormalizedLandmark(
                    x=float(landmark.x),
                    y=float(landmark.y),
                )
                for landmark in hand_landmarks
            ]
            fingertips.extend(
                extract_fingertips_from_normalized_landmarks(
                    landmarks=normalized_landmarks,
                    frame_width=frame_width,
                    frame_height=frame_height,
                    fingertip_landmarks=fingertip_landmarks,
                ),
            )

        return fingertips

    legacy_hand_landmarks = getattr(results, "multi_hand_landmarks", None)

    if not legacy_hand_landmarks:
        return []

    fingertips = []

    for hand_landmarks in legacy_hand_landmarks:
        normalized_landmarks = extract_normalized_landmarks_from_mediapipe_hand(
            hand_landmarks,
        )
        fingertips.extend(
            extract_fingertips_from_normalized_landmarks(
                landmarks=normalized_landmarks,
                frame_width=frame_width,
                frame_height=frame_height,
                fingertip_landmarks=fingertip_landmarks,
            ),
        )

    return fingertips


def scale_fingertip_to_frame(
    *,
    fingertip: Fingertip,
    source_width: int,
    source_height: int,
    target_width: int,
    target_height: int,
) -> PianoPoint:
    """Scale a fingertip from one frame size to another."""

    if source_width <= 0 or source_height <= 0:
        msg = "source dimensions must be positive"
        raise ValueError(msg)

    if target_width <= 0 or target_height <= 0:
        msg = "target dimensions must be positive"
        raise ValueError(msg)

    scale_x = target_width / source_width
    scale_y = target_height / source_height

    x = round(fingertip.x * scale_x)
    y = round(fingertip.y * scale_y)

    x = max(0, min(target_width - 1, x))
    y = max(0, min(target_height - 1, y))

    return PianoPoint(x=x, y=y)


def create_disparity_roi_around_point(
    *,
    point: PianoPoint,
    frame_width: int,
    frame_height: int,
    radius: int = DEFAULT_FINGERTIP_ROI_RADIUS,
) -> DisparityRoi:
    """Create a clipped ROI around a disparity point."""

    if frame_width <= 0 or frame_height <= 0:
        msg = "frame dimensions must be positive"
        raise ValueError(msg)

    if radius < 0:
        msg = "radius must be non-negative"
        raise ValueError(msg)

    x1 = max(0, point.x - radius)
    y1 = max(0, point.y - radius)
    x2 = min(frame_width, point.x + radius + 1)
    y2 = min(frame_height, point.y + radius + 1)

    return DisparityRoi(
        x=x1,
        y=y1,
        width=x2 - x1,
        height=y2 - y1,
    )


def compute_roi_mean_disparity(
    *,
    disparity_frame: np.ndarray,
    roi: DisparityRoi,
) -> float:
    """Compute mean non-zero disparity inside an ROI."""

    roi_frame = disparity_frame[roi.y : roi.y2, roi.x : roi.x2]

    if roi_frame.size == 0:
        return 0.0

    valid_pixels = roi_frame[roi_frame > 0]

    if valid_pixels.size == 0:
        return 0.0

    return float(np.mean(valid_pixels))


def is_depth_press(
    *,
    mean_disparity: float,
    press_disparity_threshold: float = DEFAULT_PRESS_DISPARITY_THRESHOLD,
) -> bool:
    """Return True when local disparity is high enough to count as a press."""

    if press_disparity_threshold < 0.0:
        msg = "press_disparity_threshold must be non-negative"
        raise ValueError(msg)

    return mean_disparity >= press_disparity_threshold


def measure_fingertip_depth(
    *,
    fingertip: Fingertip,
    rgb_width: int,
    rgb_height: int,
    disparity_frame: np.ndarray,
    roi_radius: int = DEFAULT_FINGERTIP_ROI_RADIUS,
    press_disparity_threshold: float = DEFAULT_PRESS_DISPARITY_THRESHOLD,
) -> FingertipDepthSample:
    """Measure local disparity around a fingertip."""

    disparity_height, disparity_width = disparity_frame.shape[:2]

    disparity_point = scale_fingertip_to_frame(
        fingertip=fingertip,
        source_width=rgb_width,
        source_height=rgb_height,
        target_width=disparity_width,
        target_height=disparity_height,
    )
    roi = create_disparity_roi_around_point(
        point=disparity_point,
        frame_width=disparity_width,
        frame_height=disparity_height,
        radius=roi_radius,
    )
    mean_disparity = compute_roi_mean_disparity(
        disparity_frame=disparity_frame,
        roi=roi,
    )

    return FingertipDepthSample(
        fingertip=fingertip,
        disparity_point=disparity_point,
        roi=roi,
        mean_disparity=mean_disparity,
        pressed=is_depth_press(
            mean_disparity=mean_disparity,
            press_disparity_threshold=press_disparity_threshold,
        ),
    )


def measure_fingertips_depth(
    *,
    fingertips: list[Fingertip],
    rgb_width: int,
    rgb_height: int,
    disparity_frame: np.ndarray,
    roi_radius: int = DEFAULT_FINGERTIP_ROI_RADIUS,
    press_disparity_threshold: float = DEFAULT_PRESS_DISPARITY_THRESHOLD,
) -> list[FingertipDepthSample]:
    """Measure local disparity around multiple fingertips."""

    return [
        measure_fingertip_depth(
            fingertip=fingertip,
            rgb_width=rgb_width,
            rgb_height=rgb_height,
            disparity_frame=disparity_frame,
            roi_radius=roi_radius,
            press_disparity_threshold=press_disparity_threshold,
        )
        for fingertip in fingertips
    ]


def get_depth_pressed_key_indexes(
    *,
    depth_samples: list[FingertipDepthSample],
    keys: list[PianoKey],
) -> frozenset[int]:
    """Return key indexes pressed by fingertips with sufficient local depth."""

    pressed_key_indexes: set[int] = set()

    for depth_sample in depth_samples:
        if not depth_sample.pressed:
            continue

        hovered_key = find_hovered_key(
            fingertip=depth_sample.fingertip,
            keys=keys,
        )

        if hovered_key is not None:
            pressed_key_indexes.add(hovered_key.index)

    return frozenset(pressed_key_indexes)


def is_point_on_segment(
    *,
    point: PianoPoint,
    segment_start: PianoPoint,
    segment_end: PianoPoint,
) -> bool:
    """Return True when a point lies on a line segment."""

    cross_product = (point.y - segment_start.y) * (segment_end.x - segment_start.x) - (
        point.x - segment_start.x
    ) * (segment_end.y - segment_start.y)

    if cross_product != 0:
        return False

    min_x = min(segment_start.x, segment_end.x)
    max_x = max(segment_start.x, segment_end.x)
    min_y = min(segment_start.y, segment_end.y)
    max_y = max(segment_start.y, segment_end.y)

    return min_x <= point.x <= max_x and min_y <= point.y <= max_y


def is_point_inside_polygon(
    *,
    point: PianoPoint,
    polygon: tuple[PianoPoint, ...],
) -> bool:
    """Return True when a point is inside or on the edge of a polygon."""

    if len(polygon) < 3:
        msg = "polygon must contain at least three points"
        raise ValueError(msg)

    for index, current_point in enumerate(polygon):
        next_point = polygon[(index + 1) % len(polygon)]

        if is_point_on_segment(
            point=point,
            segment_start=current_point,
            segment_end=next_point,
        ):
            return True

    inside = False
    previous_point = polygon[-1]

    for current_point in polygon:
        current_y_above = current_point.y > point.y
        previous_y_above = previous_point.y > point.y

        if current_y_above != previous_y_above:
            intersection_x = (previous_point.x - current_point.x) * (
                point.y - current_point.y
            ) / (previous_point.y - current_point.y) + current_point.x

            if point.x < intersection_x:
                inside = not inside

        previous_point = current_point

    return inside


def is_point_inside_key(
    *,
    point: PianoPoint,
    key: PianoKey,
) -> bool:
    """Return True when a point is inside a virtual piano key."""

    return is_point_inside_polygon(point=point, polygon=key.points)


def find_hovered_key(
    *,
    fingertip: Fingertip,
    keys: list[PianoKey],
) -> PianoKey | None:
    """Return the first key currently under the fingertip."""

    point = PianoPoint(x=fingertip.x, y=fingertip.y)

    for key in sort_keys_for_hit_testing(keys):
        if is_point_inside_key(point=point, key=key):
            return key

    return None


def get_pressed_key_indexes(
    *,
    fingertips: list[Fingertip],
    keys: list[PianoKey],
) -> frozenset[int]:
    """Return indexes of keys touched by fingertips."""

    pressed_key_indexes: set[int] = set()

    for fingertip in fingertips:
        hovered_key = find_hovered_key(
            fingertip=fingertip,
            keys=keys,
        )

        if hovered_key is not None:
            pressed_key_indexes.add(hovered_key.index)

    return frozenset(pressed_key_indexes)


def create_piano_triggers(
    *,
    previous_state: PianoState,
    current_pressed_key_indexes: frozenset[int],
    keys: list[PianoKey],
    current_time: float,
) -> list[PianoTrigger]:
    """Create note triggers for newly pressed keys."""

    key_by_index = {key.index: key for key in keys}
    newly_pressed_key_indexes = sorted(
        current_pressed_key_indexes - previous_state.pressed_key_indexes,
    )

    triggers: list[PianoTrigger] = []

    for key_index in newly_pressed_key_indexes:
        key = key_by_index.get(key_index)

        if key is None:
            continue

        triggers.append(
            PianoTrigger(
                key_index=key.index,
                note=key.note,
                triggered_at=current_time,
            ),
        )

    return triggers


def update_piano_state(
    *,
    previous_state: PianoState,
    current_pressed_key_indexes: frozenset[int],
    triggers: list[PianoTrigger],
) -> PianoState:
    """Return updated virtual piano state."""

    last_note = previous_state.last_note

    if triggers:
        last_note = triggers[-1].note

    return PianoState(
        pressed_key_indexes=current_pressed_key_indexes,
        total_triggers=previous_state.total_triggers + len(triggers),
        last_note=last_note,
    )


def get_piano_message(
    *,
    triggers: list[PianoTrigger],
    state: PianoState,
) -> str:
    """Return a short HUD message for the virtual piano."""

    if triggers:
        notes = ", ".join(trigger.note for trigger in triggers)
        return f"Pressed: {notes}"

    if state.last_note is not None:
        return f"Last note: {state.last_note}"

    return "Move your index finger over a virtual key."


def get_note_frequency(note: str) -> float:
    """Return frequency in Hz for a supported note."""

    try:
        return NOTE_FREQUENCIES[note]
    except KeyError as error:
        msg = f"unsupported note: {note}"
        raise ValueError(msg) from error


def get_note_display_label(note: str) -> str:
    """Return a short display label for a note."""

    if note == "C5":
        return "C"

    return note


def create_note_waveform(
    *,
    frequency: float,
    duration_seconds: float = AUDIO_DURATION_SECONDS,
    sample_rate: int = AUDIO_SAMPLE_RATE,
    volume: float = AUDIO_VOLUME,
) -> np.ndarray:
    """Create a short int16 sine-wave note."""

    if frequency <= 0.0:
        msg = "frequency must be positive"
        raise ValueError(msg)

    if duration_seconds <= 0.0:
        msg = "duration_seconds must be positive"
        raise ValueError(msg)

    if sample_rate <= 0:
        msg = "sample_rate must be positive"
        raise ValueError(msg)

    if not 0.0 <= volume <= 1.0:
        msg = "volume must be between 0.0 and 1.0"
        raise ValueError(msg)

    sample_count = int(sample_rate * duration_seconds)
    time_values = np.linspace(
        0.0,
        duration_seconds,
        sample_count,
        endpoint=False,
    )

    fade_out = np.linspace(1.0, 0.0, sample_count)
    waveform = np.sin(2.0 * np.pi * frequency * time_values)
    waveform = waveform * fade_out * volume

    return (waveform * np.iinfo(np.int16).max).astype(np.int16)


def get_key_color(
    *,
    key_index: int,
    key_kind: PianoKeyKind,
    hovered_key_indexes: frozenset[int],
    triggered_key_indexes: frozenset[int],
) -> tuple[int, int, int]:
    """Return BGR color for a virtual piano key."""

    if key_index in triggered_key_indexes:
        return (0, 0, 255)

    if key_index in hovered_key_indexes:
        return (0, 180, 255)

    if key_kind == PianoKeyKind.BLACK:
        return (35, 35, 35)

    return (210, 210, 210)


def draw_text(
    frame: np.ndarray,
    text: str,
    position: tuple[int, int],
    *,
    scale: float = 0.7,
    color: tuple[int, int, int] = (255, 255, 255),
    thickness: int = 2,
) -> None:
    """Draw readable text with a dark outline."""

    cv2.putText(
        frame,
        text,
        position,
        cv2.FONT_HERSHEY_SIMPLEX,
        scale,
        (0, 0, 0),
        thickness + 2,
        cv2.LINE_AA,
    )
    cv2.putText(
        frame,
        text,
        position,
        cv2.FONT_HERSHEY_SIMPLEX,
        scale,
        color,
        thickness,
        cv2.LINE_AA,
    )


def piano_key_to_numpy_points(key: PianoKey) -> np.ndarray:
    """Convert a piano key polygon to OpenCV-compatible points."""

    return np.array(
        [[point.x, point.y] for point in key.points],
        dtype=np.int32,
    )


def draw_virtual_piano_key(
    frame: np.ndarray,
    *,
    key: PianoKey,
    hovered_key_indexes: frozenset[int],
    triggered_key_indexes: frozenset[int],
) -> None:
    """Draw a single pseudo-3D virtual piano key."""

    color = get_key_color(
        key_index=key.index,
        key_kind=key.kind,
        hovered_key_indexes=hovered_key_indexes,
        triggered_key_indexes=triggered_key_indexes,
    )
    points = piano_key_to_numpy_points(key)

    overlay = frame.copy()

    if key.index in triggered_key_indexes:
        alpha = 0.72
    elif key.index in hovered_key_indexes:
        alpha = 0.45
    else:
        alpha = 0.18

    cv2.fillConvexPoly(
        overlay,
        points,
        color,
    )
    cv2.addWeighted(
        overlay,
        alpha,
        frame,
        1.0 - alpha,
        0,
        frame,
    )

    thickness = 4 if key.index in hovered_key_indexes else 2

    cv2.polylines(
        frame,
        [points],
        isClosed=True,
        color=color,
        thickness=thickness,
        lineType=cv2.LINE_AA,
    )

    center = key.center

    label_scale = 0.72 if key.kind == PianoKeyKind.BLACK else 0.9
    label_offset_x = 18 if key.kind == PianoKeyKind.BLACK else 12

    draw_text(
        frame,
        get_note_display_label(key.note),
        (center.x - label_offset_x, center.y + 8),
        scale=label_scale,
        color=(255, 255, 255) if key.kind == PianoKeyKind.BLACK else color,
        thickness=2,
    )


def draw_virtual_piano_keys(
    frame: np.ndarray,
    *,
    keys: list[PianoKey],
    hovered_key_indexes: frozenset[int],
    triggered_key_indexes: frozenset[int],
) -> None:
    """Draw all virtual piano keys."""

    for key in sorted(
        keys,
        key=lambda piano_key: 0 if piano_key.kind == PianoKeyKind.WHITE else 1,
    ):
        draw_virtual_piano_key(
            frame,
            key=key,
            hovered_key_indexes=hovered_key_indexes,
            triggered_key_indexes=triggered_key_indexes,
        )


def draw_fingertips(
    frame: np.ndarray,
    *,
    fingertips: list[Fingertip],
) -> None:
    """Draw detected fingertips."""

    for fingertip in fingertips:
        cv2.circle(
            frame,
            (fingertip.x, fingertip.y),
            8,
            (255, 255, 255),
            -1,
            cv2.LINE_AA,
        )
        cv2.circle(
            frame,
            (fingertip.x, fingertip.y),
            12,
            (0, 180, 255),
            2,
            cv2.LINE_AA,
        )
        draw_text(
            frame,
            fingertip.label,
            (fingertip.x + 14, fingertip.y - 10),
            scale=0.45,
            color=(255, 255, 255),
            thickness=1,
        )


def draw_rgb_hud(
    frame: np.ndarray,
    *,
    fingertips: list[Fingertip],
    depth_samples: list[FingertipDepthSample],
    triggers: list[PianoTrigger],
    state: PianoState,
    audio_status_message: str,
) -> None:
    """Draw user-facing virtual piano HUD on the RGB frame."""

    message = get_piano_message(
        triggers=triggers,
        state=state,
    )
    pressed_count = sum(1 for sample in depth_samples if sample.pressed)
    max_local_disparity = max(
        (sample.mean_disparity for sample in depth_samples),
        default=0.0,
    )

    lines = [
        "Virtual Depth Piano",
        "MediaPipe fingertip + depth-assisted piano keys",
        f"Fingertips: {len(fingertips)}",
        f"Depth pressed: {pressed_count}",
        f"Max local disparity: {max_local_disparity:.1f}",
        f"Press threshold: {DEFAULT_PRESS_DISPARITY_THRESHOLD:.1f}",
        audio_status_message,
        f"Total triggers: {state.total_triggers}",
        f"Last note: {state.last_note or '--'}",
        message,
        "Q / ESC - quit",
    ]

    x = 20
    y = 34

    for index, line in enumerate(lines):
        draw_text(
            frame,
            line,
            (x, y + index * 27),
            scale=0.58,
            color=(255, 255, 255),
            thickness=1,
        )


def draw_disparity_hud(
    frame: np.ndarray,
    *,
    max_disparity: float,
) -> None:
    """Draw measurement/debug information on the disparity frame."""

    lines = [
        "Disparity debug view",
        f"Max disparity: {max_disparity:.1f}",
        "Small ROIs show fingertip depth checks",
    ]

    x = 20
    y = 34

    for index, line in enumerate(lines):
        draw_text(
            frame,
            line,
            (x, y + index * 28),
            scale=0.62,
            color=(255, 255, 255),
            thickness=1,
        )


def draw_depth_samples_on_disparity(
    frame: np.ndarray,
    *,
    depth_samples: list[FingertipDepthSample],
) -> None:
    """Draw fingertip depth measurement ROIs on the disparity frame."""

    for sample in depth_samples:
        color = (0, 0, 255) if sample.pressed else (0, 180, 255)

        cv2.rectangle(
            frame,
            (sample.roi.x, sample.roi.y),
            (sample.roi.x2, sample.roi.y2),
            color,
            2,
        )
        cv2.circle(
            frame,
            (sample.disparity_point.x, sample.disparity_point.y),
            5,
            color,
            -1,
            cv2.LINE_AA,
        )
        draw_text(
            frame,
            f"{sample.mean_disparity:.1f}",
            (sample.roi.x + 4, max(24, sample.roi.y - 8)),
            scale=0.45,
            color=color,
            thickness=1,
        )


def maybe_mirror_frame(
    frame: np.ndarray,
    *,
    mirror: bool = MIRROR_VIEW,
) -> np.ndarray:
    """Mirror a frame horizontally when mirror presentation mode is enabled."""

    if not mirror:
        return frame

    return cv2.flip(frame, 1)


def create_split_screen(
    *,
    rgb_frame: np.ndarray,
    disparity_frame: np.ndarray,
) -> np.ndarray:
    """Create a side-by-side RGB and disparity presentation frame."""

    if rgb_frame.shape[:2] != disparity_frame.shape[:2]:
        disparity_frame = cv2.resize(
            disparity_frame,
            (rgb_frame.shape[1], rgb_frame.shape[0]),
            interpolation=cv2.INTER_NEAREST,
        )

    return np.hstack((rgb_frame, disparity_frame))


def run() -> None:
    """Run the OAK-D virtual depth piano demo."""

    pipeline, max_disparity = create_rgb_disparity_pipeline()
    hand_tracker = create_hand_tracker()
    state = PianoState()

    audio_player = NoteAudioPlayer()
    audio_player.initialize(notes=DEFAULT_AUDIO_NOTES)

    try:
        with dai.Device(pipeline) as device:
            rgb_queue = device.getOutputQueue(
                name=RGB_STREAM_NAME,
                maxSize=4,
                blocking=False,
            )
            disparity_queue = device.getOutputQueue(
                name=DISPARITY_STREAM_NAME,
                maxSize=4,
                blocking=False,
            )

            cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)

            while True:
                rgb_message = rgb_queue.get()
                disparity_message = disparity_queue.get()

                rgb_frame = maybe_mirror_frame(rgb_message.getCvFrame())
                disparity_frame = maybe_mirror_frame(disparity_message.getFrame())

                rgb_height, rgb_width = rgb_frame.shape[:2]

                keys = create_virtual_piano_keyboard(
                    frame_width=rgb_width,
                    frame_height=rgb_height,
                )

                mediapipe_frame = cv2.cvtColor(
                    rgb_frame,
                    cv2.COLOR_BGR2RGB,
                )
                mediapipe_frame = np.ascontiguousarray(mediapipe_frame)

                import mediapipe as mp

                mp_image = mp.Image(
                    image_format=mp.ImageFormat.SRGB,
                    data=mediapipe_frame,
                )
                timestamp_ms = int(
                    (cv2.getTickCount() / cv2.getTickFrequency()) * 1000,
                )
                results = hand_tracker.detect_for_video(
                    mp_image,
                    timestamp_ms,
                )

                fingertips = extract_fingertips_from_mediapipe_results(
                    results=results,
                    frame_width=rgb_width,
                    frame_height=rgb_height,
                )

                hovered_key_indexes = get_pressed_key_indexes(
                    fingertips=fingertips,
                    keys=keys,
                )

                depth_samples = measure_fingertips_depth(
                    fingertips=fingertips,
                    rgb_width=rgb_width,
                    rgb_height=rgb_height,
                    disparity_frame=disparity_frame,
                )

                current_pressed_key_indexes = get_depth_pressed_key_indexes(
                    depth_samples=depth_samples,
                    keys=keys,
                )

                triggers = create_piano_triggers(
                    previous_state=state,
                    current_pressed_key_indexes=current_pressed_key_indexes,
                    keys=keys,
                    current_time=cv2.getTickCount() / cv2.getTickFrequency(),
                )
                audio_player.play_triggers(triggers)
                state = update_piano_state(
                    previous_state=state,
                    current_pressed_key_indexes=current_pressed_key_indexes,
                    triggers=triggers,
                )

                colorized_disparity = colorize_disparity_frame(
                    disparity_frame,
                    max_disparity=max_disparity,
                )

                triggered_key_indexes = frozenset(
                    trigger.key_index for trigger in triggers
                )

                draw_virtual_piano_keys(
                    rgb_frame,
                    keys=keys,
                    hovered_key_indexes=hovered_key_indexes,
                    triggered_key_indexes=triggered_key_indexes,
                )
                draw_fingertips(
                    rgb_frame,
                    fingertips=fingertips,
                )
                draw_rgb_hud(
                    rgb_frame,
                    fingertips=fingertips,
                    depth_samples=depth_samples,
                    triggers=triggers,
                    state=state,
                    audio_status_message=audio_player.status_message,
                )
                draw_disparity_hud(
                    colorized_disparity,
                    max_disparity=max_disparity,
                )
                draw_depth_samples_on_disparity(
                    colorized_disparity,
                    depth_samples=depth_samples,
                )

                split_screen = create_split_screen(
                    rgb_frame=rgb_frame,
                    disparity_frame=colorized_disparity,
                )

                cv2.imshow(WINDOW_NAME, split_screen)

                key = cv2.waitKey(1) & 0xFF

                if key in {ord("q"), 27}:
                    break

    finally:
        hand_tracker.close()
        audio_player.shutdown()
        cv2.destroyWindow(WINDOW_NAME)


if __name__ == "__main__":
    run()
