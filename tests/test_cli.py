from oak_vision_lab.cli import format_demo_info, format_demo_list, main
from oak_vision_lab.demo_registry import resolve_demo


def test_format_demo_list_contains_registered_demo() -> None:
    output = format_demo_list((resolve_demo("001"),))

    assert "001" in output
    assert "camera-preview-hud" in output
    assert "Real-time RGB camera preview" in output


def test_format_demo_info_contains_run_methods() -> None:
    output = format_demo_info(resolve_demo("007"))

    assert "Multi-Zone Reaction Game" in output
    assert "uv run oakvl run 007" in output
    assert "make demo-007" in output


def test_main_list_prints_demo_list(capsys) -> None:
    exit_code = main(["list"])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Available demos" in captured.out
    assert "multi-zone-reaction-game" in captured.out


def test_main_info_prints_demo_info(capsys) -> None:
    exit_code = main(["info", "001"])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Camera Preview HUD" in captured.out
    assert "uv run oakvl run 001" in captured.out


def test_main_doctor_prints_diagnostic_report(capsys) -> None:
    exit_code = main(["doctor"])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "oak-vision-lab environment doctor" in captured.out
    assert "Checks:" in captured.out
