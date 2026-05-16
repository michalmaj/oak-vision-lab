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
| 002 | Camera Preview HUD | Real-time RGB camera preview with FPS, status text and keyboard-controlled HUD. | [EN](examples/002_camera_preview_hud/README.md) / [PL](examples/002_camera_preview_hud/README.pl.md) |
| 003 | Depth Map Viewer | Colorful stereo disparity visualization showing depth-like scene structure in real time. | [EN](examples/003_depth_map_viewer/README.md) / [PL](examples/003_depth_map_viewer/README.pl.md) |
| 004 | RGB + Depth Split-Screen | Real-time split-screen view comparing regular RGB preview with colorful stereo disparity visualization. | [EN](examples/004_rgb_depth_split_screen/README.md) / [PL](examples/004_rgb_depth_split_screen/README.pl.md) |
| 005 | Depth Proximity Alert | Interactive disparity-based alert demo that reacts when an object gets close to the center of the camera view. | [EN](examples/005_depth_proximity_alert/README.md) / [PL](examples/005_depth_proximity_alert/README.pl.md) |

## Planned demos

- RGB + depth split-screen viewer
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

## Hardware and DepthAI compatibility

This project currently targets classic OAK-D / RVC2 devices and uses DepthAI v2.

The current baseline dependency is:

```text
depthai==2.32.0
```

DepthAI v3 support may be considered later as a separate compatibility layer.

## Status

Early development. The project is being built step by step.
