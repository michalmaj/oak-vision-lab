from oak_vision_lab import __version__


def test_package_has_version() -> None:
    assert isinstance(__version__, str)
    assert __version__
