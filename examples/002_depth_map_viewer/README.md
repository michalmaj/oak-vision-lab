# Depth Map Viewer

> A colorful real-time stereo vision demo that visualizes depth-like information from an OAK-D camera.

This demo shows how a stereo camera can estimate spatial structure from two synchronized monochrome cameras.

Instead of displaying a regular RGB image, the application visualizes disparity as a colorful heatmap-like image. This makes the scene look more like a sci-fi depth scanner than a normal camera preview.

## What it does

The application:

- opens the left and right mono camera streams,
- creates a stereo vision pipeline,
- computes a disparity map,
- normalizes disparity values for visualization,
- applies a colorful OpenCV colormap,
- displays the result in real time,
- draws a simple HUD with FPS and stream status,
- supports basic keyboard interaction.

## Why it is useful

This demo is a good introduction to stereo vision.

It helps students understand that a camera system can estimate scene structure not only from object appearance, but also from geometric differences between two camera views.

The visual result is also attractive during live demonstrations because depth-related information is immediately visible and easy to discuss.

## What you will learn

This demo introduces:

- stereo camera concepts,
- disparity maps,
- real-time frame processing,
- normalization of image values,
- OpenCV colormaps,
- HUD overlays,
- separating visualization logic from testable processing logic.

## How it works

The OAK-D camera has two monochrome cameras that observe the same scene from slightly different viewpoints.

The stereo pipeline compares those views and estimates disparity.

In simple terms:

```text
larger disparity  -> object is closer
smaller disparity -> object is farther away
```

The raw disparity image is then scaled to the 0-255 range and converted into a colorful visualization using an OpenCV colormap.

## How to run

From the repository root, you can run this demo in three ways.

Recommended CLI command:

```bash
uv run oakvl run depth-map-viewer
```

You can also use the demo number:

```bash
uv run oakvl run 002
```

Direct example entry point:

```bash
uv run python examples/002_depth_map_viewer/run.py
```

Makefile shortcut:

```bash
make demo-002
```

## Controls

```text
q  - quit the demo
h  - show/hide help text
```

## Expected result

A window should appear with a colorful real-time disparity visualization.

Nearby objects should usually produce stronger visual changes than distant background regions.

The HUD should display:

- demo title,
- FPS value,
- stream status,
- keyboard help.

## Ideas for experiments

Try modifying:

- colormap type,
- stereo preset,
- preview window title,
- HUD text,
- FPS display,
- disparity normalization,
- keyboard controls.

Possible extensions:

- add multiple colormap modes,
- add screenshot capture,
- add side-by-side raw disparity and colored view,
- add a presentation mode,
- add a simple distance-based interaction,
- add an RGB + depth split-screen view.