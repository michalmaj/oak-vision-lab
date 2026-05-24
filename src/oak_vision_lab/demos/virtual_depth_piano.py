"""Virtual depth piano geometry and interaction logic."""

from __future__ import annotations

from dataclasses import dataclass

DEFAULT_NOTES = ("C", "D", "E", "G", "A")

DEFAULT_TOP_Y_RATIO = 0.52
DEFAULT_BOTTOM_Y_RATIO = 0.92
DEFAULT_BACK_WIDTH_RATIO = 0.68
DEFAULT_FRONT_WIDTH_RATIO = 0.96


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
            ),
        )

    return keys


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

    for key in keys:
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
