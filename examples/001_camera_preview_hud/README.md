# OAK-D Camera Preview HUD

> A colorful real-time camera preview demo for classic OAK-D devices using DepthAI v2.

This demo shows a live RGB camera stream from an OAK-D device with a simple on-screen HUD.

It is designed as the first interactive demo in `oak-vision-lab`.

## What it does

The application:

- opens the OAK-D RGB camera stream,
- displays a live OpenCV preview window,
- draws a colorful HUD overlay,
- shows FPS information,
- displays camera stream status,
- supports simple keyboard interaction.

## What you will learn

This demo introduces:

- basic DepthAI v2 pipeline creation,
- RGB camera preview streaming,
- OpenCV real-time display,
- simple HUD rendering,
- FPS calculation,
- basic keyboard controls,
- separating testable logic from hardware-dependent code.

## Hardware compatibility

This demo targets classic OAK-D / RVC2 devices.

It uses:

```text
depthai==2.32.0
```

DepthAI v3 is not used in this demo because some older OAK-D devices may have compatibility issues with the newer API and calibration handling.

## Requirements

- OAK-D camera,
- Python environment managed by `uv`,
- USB connection to the camera,
- project dependencies installed with `uv sync`.

## How to run

From the repository root, you can run this demo in three ways.

Recommended CLI command:

```bash
uv run oakvl run camera-preview-hud
```

You can also use the demo number:

```bash
uv run oakvl run 001
```

Direct example entry point:

```bash
uv run python examples/001_camera_preview_hud/run.py
```

Makefile shortcut:

```bash
make demo-001
```

## Controls

| Key | Action |
| --- | --- |
| `q` | Quit the demo |
| `h` | Show or hide help text |

## Expected result

A live camera preview window should appear.

The window should display:

- the RGB stream from the OAK-D camera,
- the project title,
- FPS value,
- stream status,
- keyboard help.

## Troubleshooting

### The camera does not start

Check that:

- the OAK-D camera is connected via USB,
- no other application is using the camera,
- the correct DepthAI version is installed,
- the device is visible to the system.

You can check the installed DepthAI version with:

```bash
uv run python -c "import depthai as dai; print(dai.__version__)"
```

Expected version:

```text
2.32.0.0
```

### The OpenCV window does not appear

Make sure that:

- the script is running on a system with GUI support,
- OpenCV is installed,
- the application is not running inside a headless terminal environment.

### The FPS is unstable

This is normal during live camera streaming.

FPS can depend on:

- USB speed,
- lighting conditions,
- system load,
- camera configuration,
- preview resolution.

## Ideas for experiments

Try modifying:

- preview resolution,
- HUD text,
- text position,
- font scale,
- FPS display,
- keyboard controls,
- background effects.

Possible extensions:

- add a recording mode,
- add screenshot capture,
- add a colorful frame border,
- add a presentation mode,
- add visual effects controlled by keyboard keys.
