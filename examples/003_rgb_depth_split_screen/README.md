# RGB + Depth Split-Screen

> A real-time split-screen demo showing the regular RGB camera view next to a colorful stereo disparity visualization.

This demo combines two perspectives from the OAK-D camera system:

- the standard RGB camera preview,
- a colorful stereo disparity view.

The goal is to make it easy to compare what a normal camera sees with what a stereo vision pipeline can extract from the scene geometry.

## What it does

The application:

- opens an RGB camera stream,
- opens left and right mono camera streams,
- creates a stereo disparity pipeline,
- visualizes disparity with an OpenCV colormap,
- displays RGB and disparity views side by side,
- adds labels to both panels,
- draws a simple HUD with FPS and stream status,
- supports basic keyboard interaction.

## Why it is useful

This demo is useful because it shows two different ways of looking at the same scene.

The RGB view is intuitive and familiar.  
The disparity view reveals spatial structure and makes nearby and distant regions visually distinct.

During workshops or live presentations, this split-screen layout makes it easy to explain that computer vision systems can use more than just color and texture. They can also use geometry.

## What you will learn

This demo introduces:

- RGB camera streaming,
- stereo disparity visualization,
- side-by-side frame composition,
- OpenCV image resizing,
- OpenCV colormaps,
- panel labeling,
- real-time HUD overlays,
- simple keyboard controls,
- combining multiple camera streams in one application.

## How it works

The demo builds a pipeline with:

```text
RGB camera stream        -> left panel
Left + right mono camera -> stereo pipeline -> disparity map -> right panel
```

The disparity map is normalized to the 0-255 range and then converted into a colorful visualization.

The RGB frame and the colorized disparity frame are resized to compatible dimensions and joined horizontally into one split-screen view.

## How to run

From the repository root, you can run this demo in three ways.

Recommended CLI command:

```bash
uv run oakvl run rgb-depth-split-screen
```

You can also use the demo number:

```bash
uv run oakvl run 003
```

Direct example entry point:

```bash
uv run python examples/003_rgb_depth_split_screen/run.py
```

Makefile shortcut:

```bash
make demo-003
```

## Controls

```text
q  - quit the demo
h  - show/hide help text
```

## Expected result

A window should appear with two panels:

```text
+----------------------+----------------------+
| RGB camera           | Stereo disparity     |
|                      |                      |
| normal camera view   | colorful depth-like  |
|                      | visualization        |
+----------------------+----------------------+
```

The HUD should display:

- demo title,
- FPS value,
- stream status,
- keyboard help.

## Ideas for experiments

Try modifying:

- panel labels,
- colormap type,
- RGB preview size,
- stereo preset,
- HUD position,
- FPS display,
- split-screen layout.

Possible extensions:

- add vertical split-screen mode,
- add a key for switching colormaps,
- add screenshot capture,
- add RGB-only and disparity-only modes,
- add a presentation mode with larger text,
- add a third panel with raw disparity,
- add simple interaction based on the closest visible object.