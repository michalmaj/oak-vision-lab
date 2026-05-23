"""Depth music playground logic based on stereo disparity zones."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from oak_vision_lab.depth.proximity import ProximityLevel

DEFAULT_ZONE_COUNT = 5
DEFAULT_TRIGGER_COOLDOWN_SECONDS = 0.35

DEFAULT_NEAR_THRESHOLD = 25.0
DEFAULT_VERY_CLOSE_THRESHOLD = 45.0

DEFAULT_NOTES = ("C", "D", "E", "G", "A")


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
