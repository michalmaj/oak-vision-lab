"""Reusable HUD helpers for OpenCV-based demos."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HudConfig:
    """Configuration of the on-screen HUD overlay.

    This class is intentionally simple and testable without an OAK-D camera.
    It allows CI tests to validate HUD-related logic without requiring
    physical hardware.
    """

    title: str = "oak-vision-lab"
    show_fps: bool = True
    show_help: bool = True
    show_status: bool = True


def build_hud_lines(config: HudConfig, fps: float | None, status: str) -> list[str]:
    """Build text lines displayed in the HUD.

    This function does not draw anything on the image. It only prepares
    display text, which makes it easy to test automatically.
    """

    lines = [config.title]

    if config.show_fps and fps is not None:
        lines.append(f"FPS: {fps:.1f}")

    if config.show_status:
        lines.append(f"Status: {status}")

    if config.show_help:
        lines.append("Keys: q = quit, h = toggle help")

    return lines
