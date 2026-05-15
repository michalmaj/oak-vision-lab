# oak-vision-lab

[![CI](https://github.com/michalpmaj/oak-vision-lab/actions/workflows/ci.yml/badge.svg)](https://github.com/michalpmaj/oak-vision-lab/actions/workflows/ci.yml)

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

## Planned demos

- OAK-D camera preview with a colorful HUD
- Depth map viewer
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

## Status

Early development. The project is being built step by step.
