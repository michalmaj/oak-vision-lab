import pytest

from oak_vision_lab.demo_registry import list_demos, resolve_demo


def test_list_demos_returns_registered_demos() -> None:
    demos = list_demos()

    assert len(demos) == 8
    assert demos[0].number == "001"
    assert demos[-1].number == "008"


def test_resolve_demo_by_number() -> None:
    demo = resolve_demo("001")

    assert demo.slug == "camera-preview-hud"


def test_resolve_demo_by_slug() -> None:
    demo = resolve_demo("multi-zone-reaction-game")

    assert demo.number == "007"


def test_resolve_demo_strips_whitespace_and_ignores_case() -> None:
    demo = resolve_demo("  DEPTH-MAP-VIEWER  ")

    assert demo.number == "002"


def test_resolve_demo_rejects_unknown_demo() -> None:
    with pytest.raises(ValueError, match="Unknown demo"):
        resolve_demo("unknown-demo")
