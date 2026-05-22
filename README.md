# oak-vision-lab

[![CI](https://github.com/michalmaj/oak-vision-lab/actions/workflows/ci.yml/badge.svg)](https://github.com/michalmaj/oak-vision-lab/actions/workflows/ci.yml)

> Interactive computer vision demos for OAK-D cameras, designed for education, workshops, and live presentations.

[Polska wersja](README.pl.md)

`oak-vision-lab` is a growing collection of colorful, interactive, and educational computer vision demos built with Python and OAK-D cameras.

The project is designed as:

- a teaching resource for students,
- a showcase repository demonstrating clean engineering practices,
- a playground for live computer vision presentations.

## Goals

- Build interactive demos that are fun to use and easy to explain.
- Teach computer vision concepts through small, focused examples.
- Use a professional repository workflow with branches, pull requests, tests, and CI.
- Keep the project readable, maintainable, and portfolio-friendly.
- Support both small hands-on groups and larger live audiences.

## Tech stack

- Python
- OAK-D / DepthAI
- OpenCV
- uv
- Ruff
- pytest
- GitHub Actions

## Available demos

| No. | Demo | Description | Documentation |
| --- | --- | --- | --- |
| 001 | Camera Preview HUD | Real-time RGB camera preview with FPS, status text and keyboard-controlled HUD. | [EN](examples/001_camera_preview_hud/README.md) / [PL](examples/001_camera_preview_hud/README.pl.md) |
| 002 | Depth Map Viewer | Colorful stereo disparity visualization showing depth-like scene structure in real time. | [EN](examples/002_depth_map_viewer/README.md) / [PL](examples/002_depth_map_viewer/README.pl.md) |
| 003 | RGB + Depth Split-Screen | Real-time split-screen view comparing regular RGB preview with colorful stereo disparity visualization. | [EN](examples/003_rgb_depth_split_screen/README.md) / [PL](examples/003_rgb_depth_split_screen/README.pl.md) |
| 004 | Depth Proximity Alert | Interactive disparity-based alert demo that reacts when an object gets close to the center of the camera view. | [EN](examples/004_depth_proximity_alert/README.md) / [PL](examples/004_depth_proximity_alert/README.pl.md) |
| 005 | Depth Hot Zone Game | Real-time mini-game where the player scores points by moving a hand or object into a depth-based hot zone. | [EN](examples/005_depth_hot_zone_game/README.md) / [PL](examples/005_depth_hot_zone_game/README.pl.md) |
| 006 | Moving Depth Target Game | Real-time mini-game where the player scores points by reaching randomly positioned depth-based target zones. | [EN](examples/006_moving_depth_target_game/README.md) / [PL](examples/006_moving_depth_target_game/README.pl.md) |
| 007 | Multi-Zone Reaction Game | Real-time reaction game where the player scores points by reaching the currently active depth-based zone. | [EN](examples/007_multi_zone_reaction_game/README.md) / [PL](examples/007_multi_zone_reaction_game/README.pl.md) |

## Planned demos

- Multi-zone reaction game
- RGB + depth presentation mode
- Object detection demo
- People counter
- Hand interaction demo
- Gesture-controlled interface
- Computer vision mini-games

## Project workflow

This repository follows a commercial-style development workflow:

- each feature is developed on a separate branch,
- changes are reviewed through pull requests,
- commits are small and meaningful,
- tests and code quality checks are automated,
- documentation is updated together with code.

Example branch names:

```text
feature/001-project-bootstrap
feature/002-camera-preview-hud
feature/003-depth-map-viewer
docs/004-demo-readme-template
fix/005-camera-error-handling
```

## Local notes

Private local notes, scratch files, and ChatGPT conversation links can be stored in:

```text
local/
```

This directory is ignored by Git.

## Development

Install dependencies:

```bash
uv sync
```

Run tests:

```bash
uv run pytest
```

Run Ruff checks:

```bash
uv run ruff check .
```

Format code:

```bash
uv run ruff format .
```

## Makefile shortcuts

The project can be used directly with `uv`, but a `Makefile` is also provided as a convenience layer for common development commands and demo runs.

The Makefile does not replace `uv`. It only wraps common `uv` commands.

List available shortcuts:

```bash
make help
```

Install or sync dependencies:

```bash
make sync
```

Run quality checks:

```bash
make check
```

List available demos:

```bash
make demos
```

Run a demo:

```bash
make demo-001
make demo-007
```

Run software environment diagnostics:

```bash
make doctor
```

Run diagnostics including OAK-D device discovery:

```bash
make doctor-device
```

Direct `uv` commands remain the most explicit way to run demos, for example:

```bash
uv run python examples/007_multi_zone_reaction_game/run.py
```

## CLI demo runner

The project also provides a small command line interface for listing, inspecting and running demos.

The CLI is available through the `oakvl` command:

```bash
uv run oakvl --help
```

List available demos:

```bash
uv run oakvl list
```

Check the local software environment:

```bash
uv run oakvl doctor
```

Check the software environment and OAK-D / DepthAI device discovery:

```bash
uv run oakvl doctor --device
```

The default doctor command verifies the Python version and checks whether key packages such as DepthAI, OpenCV, NumPy, pytest and Ruff can be imported.

The `--device` option additionally checks whether a DepthAI device can be discovered. This check is optional because it requires hardware access and should not be required in CI.

Show details about a selected demo:

```bash
uv run oakvl info 001
uv run oakvl info multi-zone-reaction-game
```

Run a demo by number:

```bash
uv run oakvl run 001
```

Run a demo by slug:

```bash
uv run oakvl run multi-zone-reaction-game
```

Each demo can now be run in three ways:

```bash
uv run oakvl run 007
uv run python examples/007_multi_zone_reaction_game/run.py
make demo-007
```

The direct `uv run python examples/.../run.py` form remains useful for teaching because it clearly shows where the example entry point is located.

The `oakvl` CLI is the most stable interface for regular use because demo names can stay consistent even if internal paths change later.

## Hardware and DepthAI compatibility

This project currently targets classic OAK-D / RVC2 devices and uses DepthAI v2.

The current baseline dependency is:

```text
depthai==2.32.0
```

DepthAI v3 support may be considered later as a separate compatibility layer.

## Status

Early development. The project is being built step by step.
