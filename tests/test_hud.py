from oak_vision_lab.visualization.hud import HudConfig, build_hud_lines


def test_build_hud_lines_contains_title() -> None:
    config = HudConfig(title="Test Demo")

    lines = build_hud_lines(config, fps=30.0, status="running")

    assert lines[0] == "Test Demo"


def test_build_hud_lines_formats_fps() -> None:
    config = HudConfig(show_fps=True)

    lines = build_hud_lines(config, fps=29.987, status="running")

    assert "FPS: 30.0" in lines


def test_build_hud_lines_can_hide_help() -> None:
    config = HudConfig(show_help=False)

    lines = build_hud_lines(config, fps=30.0, status="running")

    assert all("Keys:" not in line for line in lines)
