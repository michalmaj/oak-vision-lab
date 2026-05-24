"""Depth music playground demo based on RGB preview and stereo disparity zones."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import cv2
import depthai as dai
import numpy as np

from oak_vision_lab.depth.disparity import colorize_disparity_frame
from oak_vision_lab.depth.proximity import ProximityLevel, classify_proximity

WINDOW_NAME = "oak-vision-lab | Depth Music Playground"

RGB_STREAM_NAME = "rgb"
DISPARITY_STREAM_NAME = "disparity"

DEFAULT_ZONE_COUNT = 5
DEFAULT_TRIGGER_COOLDOWN_SECONDS = 0.35

DEFAULT_NEAR_THRESHOLD = 25.0
DEFAULT_VERY_CLOSE_THRESHOLD = 45.0

DEFAULT_NOTES = ("C", "D", "E", "G", "A")

NOTE_FREQUENCIES = {
    "C": 261.63,
    "D": 293.66,
    "E": 329.63,
    "G": 392.00,
    "A": 440.00,
}

AUDIO_SAMPLE_RATE = 44_100
AUDIO_DURATION_SECONDS = 0.18
AUDIO_VOLUME = 0.35

RGB_PREVIEW_WIDTH = 640
RGB_PREVIEW_HEIGHT = 400


@dataclass(frozen=True)
class MusicZone:
    """Rectangular interactive music zone in image coordinates."""

    index: int
    note: str
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
class ZoneMeasurement:
    """Measurement result for a single music zone."""

    zone: MusicZone
    mean_disparity: float
    proximity_level: ProximityLevel
    active: bool


@dataclass(frozen=True)
class NoteTrigger:
    """Triggered music note event."""

    zone_index: int
    note: str
    mean_disparity: float
    triggered_at: float


@dataclass(frozen=True)
class MusicPlaygroundState:
    """State of the depth music playground."""

    total_triggers: int = 0
    last_trigger_time_by_zone: dict[int, float] | None = None
    last_note: str | None = None


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


def create_music_zones(
    *,
    frame_width: int,
    frame_height: int,
    notes: tuple[str, ...] = DEFAULT_NOTES,
    top_margin_ratio: float = 0.25,
    bottom_margin_ratio: float = 0.12,
) -> list[MusicZone]:
    """Create horizontal music zones across the frame."""

    if frame_width <= 0 or frame_height <= 0:
        msg = "frame dimensions must be positive"
        raise ValueError(msg)

    if not notes:
        msg = "notes must not be empty"
        raise ValueError(msg)

    zone_count = len(notes)
    usable_y = int(frame_height * top_margin_ratio)
    usable_height = int(frame_height * (1.0 - top_margin_ratio - bottom_margin_ratio))

    if usable_height <= 0:
        msg = "usable zone height must be positive"
        raise ValueError(msg)

    zone_width = frame_width // zone_count
    zones: list[MusicZone] = []

    for index, note in enumerate(notes):
        x = index * zone_width

        width = frame_width - x if index == zone_count - 1 else zone_width

        zones.append(
            MusicZone(
                index=index,
                note=note,
                x=x,
                y=usable_y,
                width=width,
                height=usable_height,
            ),
        )

    return zones


def compute_zone_mean_disparity(
    disparity_frame: np.ndarray,
    zone: MusicZone,
) -> float:
    """Compute mean non-zero disparity inside a music zone."""

    roi = disparity_frame[zone.y : zone.y2, zone.x : zone.x2]

    if roi.size == 0:
        return 0.0

    valid_pixels = roi[roi > 0]

    if valid_pixels.size == 0:
        return 0.0

    return float(np.mean(valid_pixels))


def is_zone_active(
    proximity_level: ProximityLevel,
) -> bool:
    """Return True when a music zone should be considered active."""

    return proximity_level in {
        ProximityLevel.NEAR,
        ProximityLevel.VERY_CLOSE,
    }


def should_trigger_note(
    *,
    zone_index: int,
    current_time: float,
    last_trigger_time_by_zone: dict[int, float],
    cooldown_seconds: float = DEFAULT_TRIGGER_COOLDOWN_SECONDS,
) -> bool:
    """Return True when a zone can trigger a note event."""

    if cooldown_seconds < 0.0:
        msg = "cooldown_seconds must be non-negative"
        raise ValueError(msg)

    last_trigger_time = last_trigger_time_by_zone.get(zone_index)

    if last_trigger_time is None:
        return True

    return current_time - last_trigger_time >= cooldown_seconds


def create_note_triggers(
    *,
    measurements: list[ZoneMeasurement],
    current_time: float,
    last_trigger_time_by_zone: dict[int, float],
    cooldown_seconds: float = DEFAULT_TRIGGER_COOLDOWN_SECONDS,
) -> list[NoteTrigger]:
    """Create note trigger events from active zone measurements."""

    triggers: list[NoteTrigger] = []

    for measurement in measurements:
        if not measurement.active:
            continue

        if not should_trigger_note(
            zone_index=measurement.zone.index,
            current_time=current_time,
            last_trigger_time_by_zone=last_trigger_time_by_zone,
            cooldown_seconds=cooldown_seconds,
        ):
            continue

        triggers.append(
            NoteTrigger(
                zone_index=measurement.zone.index,
                note=measurement.zone.note,
                mean_disparity=measurement.mean_disparity,
                triggered_at=current_time,
            ),
        )

    return triggers


def update_music_state(
    *,
    state: MusicPlaygroundState,
    triggers: list[NoteTrigger],
) -> MusicPlaygroundState:
    """Return updated music playground state after note triggers."""

    last_trigger_time_by_zone = dict(state.last_trigger_time_by_zone or {})
    last_note = state.last_note

    for trigger in triggers:
        last_trigger_time_by_zone[trigger.zone_index] = trigger.triggered_at
        last_note = trigger.note

    return MusicPlaygroundState(
        total_triggers=state.total_triggers + len(triggers),
        last_trigger_time_by_zone=last_trigger_time_by_zone,
        last_note=last_note,
    )


def get_zone_intensity(
    *,
    mean_disparity: float,
    max_disparity: float,
) -> float:
    """Return normalized visual intensity for a music zone."""

    if max_disparity <= 0.0:
        return 0.0

    normalized = mean_disparity / max_disparity

    return max(0.0, min(1.0, normalized))


def get_music_message(
    *,
    triggers: list[NoteTrigger],
    state: MusicPlaygroundState,
) -> str:
    """Return a short HUD message for the music playground."""

    if triggers:
        notes = ", ".join(trigger.note for trigger in triggers)
        return f"Triggered: {notes}"

    if state.last_note is not None:
        return f"Last note: {state.last_note}"

    return "Move a hand or object into a zone to trigger notes."


def get_note_frequency(note: str) -> float:
    """Return frequency in Hz for a supported note."""

    try:
        return NOTE_FREQUENCIES[note]
    except KeyError as error:
        msg = f"unsupported note: {note}"
        raise ValueError(msg) from error


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


class NoteAudioPlayer:
    """Small pygame-based note player for the depth music playground."""

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

    def initialize(self, *, notes: tuple[str, ...] = DEFAULT_NOTES) -> None:
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

    def play_triggers(self, triggers: list[NoteTrigger]) -> None:
        """Play all triggered notes."""

        for trigger in triggers:
            self.play_note(trigger.note)

    def shutdown(self) -> None:
        """Shutdown pygame mixer if it was initialized."""

        if self._pygame is None:
            return

        if self._pygame.mixer.get_init():
            self._pygame.mixer.quit()


def measure_music_zones(
    *,
    disparity_frame: np.ndarray,
    zones: list[MusicZone],
) -> list[ZoneMeasurement]:
    """Measure all music zones in a disparity frame."""

    measurements: list[ZoneMeasurement] = []

    for zone in zones:
        mean_disparity = compute_zone_mean_disparity(
            disparity_frame,
            zone,
        )
        proximity_level = classify_proximity(
            mean_disparity=mean_disparity,
            near_threshold=DEFAULT_NEAR_THRESHOLD,
            very_close_threshold=DEFAULT_VERY_CLOSE_THRESHOLD,
        )

        measurements.append(
            ZoneMeasurement(
                zone=zone,
                mean_disparity=mean_disparity,
                proximity_level=proximity_level,
                active=is_zone_active(proximity_level),
            ),
        )

    return measurements


def scale_music_zone(
    *,
    zone: MusicZone,
    source_width: int,
    source_height: int,
    target_width: int,
    target_height: int,
) -> MusicZone:
    """Scale a music zone from one frame size to another."""

    if source_width <= 0 or source_height <= 0:
        msg = "source dimensions must be positive"
        raise ValueError(msg)

    if target_width <= 0 or target_height <= 0:
        msg = "target dimensions must be positive"
        raise ValueError(msg)

    scale_x = target_width / source_width
    scale_y = target_height / source_height

    return MusicZone(
        index=zone.index,
        note=zone.note,
        x=round(zone.x * scale_x),
        y=round(zone.y * scale_y),
        width=round(zone.width * scale_x),
        height=round(zone.height * scale_y),
    )


def scale_music_zones(
    *,
    zones: list[MusicZone],
    source_width: int,
    source_height: int,
    target_width: int,
    target_height: int,
) -> list[MusicZone]:
    """Scale music zones from one frame size to another."""

    return [
        scale_music_zone(
            zone=zone,
            source_width=source_width,
            source_height=source_height,
            target_width=target_width,
            target_height=target_height,
        )
        for zone in zones
    ]


def get_zone_color(
    *,
    proximity_level: ProximityLevel,
    active: bool,
) -> tuple[int, int, int]:
    """Return BGR color for a music zone."""

    if not active:
        return (120, 120, 120)

    colors = {
        ProximityLevel.SAFE: (120, 120, 120),
        ProximityLevel.NEAR: (0, 180, 255),
        ProximityLevel.VERY_CLOSE: (0, 0, 255),
    }

    return colors[proximity_level]


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


def draw_music_zone(
    frame: np.ndarray,
    *,
    measurement: ZoneMeasurement,
    max_disparity: float,
    recently_triggered: bool,
) -> None:
    """Draw a music zone with visual intensity."""

    zone = measurement.zone
    intensity = get_zone_intensity(
        mean_disparity=measurement.mean_disparity,
        max_disparity=max_disparity,
    )
    color = get_zone_color(
        proximity_level=measurement.proximity_level,
        active=measurement.active,
    )

    overlay = frame.copy()

    fill_alpha = 0.12 + 0.38 * intensity
    if recently_triggered:
        fill_alpha = 0.65

    cv2.rectangle(
        overlay,
        (zone.x, zone.y),
        (zone.x2, zone.y2),
        color,
        -1,
    )
    cv2.addWeighted(
        overlay,
        fill_alpha,
        frame,
        1.0 - fill_alpha,
        0,
        frame,
    )

    thickness = 4 if recently_triggered else 2
    cv2.rectangle(
        frame,
        (zone.x, zone.y),
        (zone.x2, zone.y2),
        color,
        thickness,
    )

    note_label = f"{zone.note}"
    value_label = f"{measurement.mean_disparity:.1f}"

    draw_text(
        frame,
        note_label,
        (zone.x + 16, zone.y + 42),
        scale=1.0,
        color=color,
        thickness=3,
    )
    draw_text(
        frame,
        value_label,
        (zone.x + 16, zone.y + 76),
        scale=0.55,
        color=(255, 255, 255),
        thickness=1,
    )


def draw_music_zones(
    frame: np.ndarray,
    *,
    measurements: list[ZoneMeasurement],
    max_disparity: float,
    recently_triggered_zone_indexes: set[int],
) -> None:
    """Draw all music zones."""

    for measurement in measurements:
        draw_music_zone(
            frame,
            measurement=measurement,
            max_disparity=max_disparity,
            recently_triggered=measurement.zone.index
            in recently_triggered_zone_indexes,
        )


def draw_rgb_hud(
    frame: np.ndarray,
    *,
    triggers: list[NoteTrigger],
    state: MusicPlaygroundState,
    audio_status_message: str,
) -> None:
    """Draw user-facing music playground information on the RGB frame."""

    message = get_music_message(triggers=triggers, state=state)

    lines = [
        "Depth Music Playground",
        "RGB HUD + disparity-based zone triggers",
        f"Total triggers: {state.total_triggers}",
        f"Last note: {state.last_note or '--'}",
        audio_status_message,
        message,
        "R - reset state | Q / ESC - quit",
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


def draw_disparity_hud(
    frame: np.ndarray,
    *,
    max_disparity: float,
) -> None:
    """Draw measurement/debug information on the disparity frame."""

    lines = [
        "Disparity music zones",
        f"Notes: {' '.join(DEFAULT_NOTES)}",
        f"Max disparity: {max_disparity:.1f}",
        "Active zones trigger visual notes",
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
    """Run the OAK-D depth music playground demo."""

    pipeline, max_disparity = create_rgb_disparity_pipeline()

    audio_player = NoteAudioPlayer()
    audio_player.initialize(notes=DEFAULT_NOTES)

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

        state = MusicPlaygroundState()

        while True:
            rgb_message = rgb_queue.get()
            disparity_message = disparity_queue.get()

            rgb_frame = rgb_message.getCvFrame()
            disparity_frame = disparity_message.getFrame()

            disparity_height, disparity_width = disparity_frame.shape[:2]
            rgb_height, rgb_width = rgb_frame.shape[:2]

            disparity_zones = create_music_zones(
                frame_width=disparity_width,
                frame_height=disparity_height,
            )
            measurements = measure_music_zones(
                disparity_frame=disparity_frame,
                zones=disparity_zones,
            )

            current_time = time.monotonic()
            triggers = create_note_triggers(
                measurements=measurements,
                current_time=current_time,
                last_trigger_time_by_zone=state.last_trigger_time_by_zone or {},
            )

            audio_player.play_triggers(triggers)

            state = update_music_state(
                state=state,
                triggers=triggers,
            )

            recently_triggered_zone_indexes = {
                trigger.zone_index for trigger in triggers
            }

            rgb_zones = scale_music_zones(
                zones=disparity_zones,
                source_width=disparity_width,
                source_height=disparity_height,
                target_width=rgb_width,
                target_height=rgb_height,
            )
            rgb_measurements = [
                ZoneMeasurement(
                    zone=rgb_zone,
                    mean_disparity=measurement.mean_disparity,
                    proximity_level=measurement.proximity_level,
                    active=measurement.active,
                )
                for rgb_zone, measurement in zip(
                    rgb_zones,
                    measurements,
                    strict=True,
                )
            ]

            colorized_disparity = colorize_disparity_frame(
                disparity_frame,
                max_disparity=max_disparity,
            )

            draw_music_zones(
                rgb_frame,
                measurements=rgb_measurements,
                max_disparity=max_disparity,
                recently_triggered_zone_indexes=recently_triggered_zone_indexes,
            )
            draw_music_zones(
                colorized_disparity,
                measurements=measurements,
                max_disparity=max_disparity,
                recently_triggered_zone_indexes=recently_triggered_zone_indexes,
            )
            draw_rgb_hud(
                rgb_frame,
                triggers=triggers,
                state=state,
                audio_status_message=audio_player.status_message,
            )
            draw_disparity_hud(
                colorized_disparity,
                max_disparity=max_disparity,
            )

            split_screen = create_split_screen(
                rgb_frame=rgb_frame,
                disparity_frame=colorized_disparity,
            )

            cv2.imshow(WINDOW_NAME, split_screen)

            key = cv2.waitKey(1) & 0xFF

            if key in {ord("q"), 27}:
                break

            if key == ord("r"):
                state = MusicPlaygroundState()

    audio_player.shutdown()
    cv2.destroyWindow(WINDOW_NAME)


if __name__ == "__main__":
    run()
