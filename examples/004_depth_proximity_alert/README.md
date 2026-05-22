# Depth Proximity Alert

> A real-time interactive demo that reacts when an object gets close to the camera.

This demo uses stereo disparity information to estimate whether something is close to the center of the camera view.

It turns the depth-like visualization into a simple interactive alert system with three states:

```text
SAFE -> NEAR -> VERY CLOSE
```

## What it does

The application:

- creates a stereo disparity pipeline,
- visualizes disparity with an OpenCV colormap,
- extracts a centered region of interest,
- computes the mean disparity inside that region,
- classifies proximity into three levels,
- draws a colored region of interest,
- draws an alert border around the frame,
- displays FPS and status in the HUD,
- reacts in real time when an object moves closer to the camera.

## Why it is useful

This demo shows how raw visual information can be transformed into a simple decision.

Instead of only displaying an image, the application interprets part of the scene and produces a readable state.

This makes it a good introduction to:

- perception-based interaction,
- threshold-based decision logic,
- region-of-interest processing,
- real-time visual feedback.

It is also fun during live demos because people can move their hand or an object toward the camera and immediately see the system react.

## What you will learn

This demo introduces:

- stereo disparity visualization,
- center region-of-interest extraction,
- simple image statistics,
- mean disparity calculation,
- threshold-based classification,
- visual alert overlays,
- separating testable decision logic from camera-dependent code.

## How it works

The demo uses the disparity frame produced by the stereo pipeline.

A centered region of interest is extracted from the frame:

```text
+-------------------------+
|                         |
|         +-------+       |
|         |  ROI  |       |
|         +-------+       |
|                         |
+-------------------------+
```

The mean disparity is computed inside that region.

Higher disparity usually means that an object is closer to the camera.

The mean value is then classified into one of three states:

```text
low disparity      -> SAFE
medium disparity   -> NEAR
high disparity     -> VERY CLOSE
```

The current state changes the visual alert color and the HUD status.

## How to run

From the repository root, you can run this demo in three ways.

Recommended CLI command:

```bash
uv run oakvl run depth-proximity-alert
```

You can also use the demo number:

```bash
uv run oakvl run 004
```

Direct example entry point:

```bash
uv run python examples/004_depth_proximity_alert/run.py
```

Makefile shortcut:

```bash
make demo-004
```

## Controls

```text
q  - quit the demo
h  - show/hide help text
```

## Expected result

A window should appear with a colorful disparity visualization.

In the center of the image, a region of interest should be visible.

When an object moves closer to the center region:

- the status should change,
- the ROI color should change,
- the frame border should change.

## Ideas for experiments

Try modifying:

- ROI size,
- proximity thresholds,
- alert colors,
- border thickness,
- HUD status text,
- colormap type.

Possible extensions:

- add sound alerts,
- add a calibration screen,
- add keyboard controls for thresholds,
- add multiple regions of interest,
- add a closest-object indicator,
- add a simple game based on moving closer or farther away.