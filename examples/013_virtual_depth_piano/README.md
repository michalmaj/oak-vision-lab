# 013 — Virtual Depth Piano

Virtual Depth Piano is an interactive OAK-D demo that combines RGB preview, MediaPipe hand tracking, stereo disparity and pygame audio.

The demo draws pseudo-3D piano keys on the RGB camera view. MediaPipe detects the index fingertip, and stereo disparity is used as an additional depth signal to decide whether a hovered key is actually pressed.

## What it demonstrates

- RGB preview as a user-facing HUD
- Pseudo-3D virtual piano keys
- MediaPipe hand tracking
- Fingertip-based key hover detection
- Depth-assisted key press detection
- Local disparity measurement around the fingertip
- Split-screen RGB + disparity presentation
- pygame-based generated note sounds
- Testable geometry and interaction logic separated from camera input

## Required local model

This demo uses MediaPipe Tasks Hand Landmarker and requires a local model file:

```text
models/mediapipe/hand_landmarker.task
```

The model file is not committed to the repository. Place the downloaded `hand_landmarker.task` file in that path before running the demo.

The `models/mediapipe/*.task` path is ignored by Git because the model is a binary asset.

## How it works

The RGB frame is used as the main presentation layer. A set of pseudo-3D piano keys is drawn near the bottom of the frame:

```text
C  D  E  G  A
```

MediaPipe detects the index fingertip in RGB coordinates. The fingertip is tested against the virtual key polygons to determine hover state.

For depth-assisted pressing, the fingertip position is scaled to the disparity frame. A small local ROI is sampled around that point. If the local mean disparity is above the press threshold, the hovered key is treated as pressed and a note is triggered.

The disparity view on the right shows the depth/debug layer, including the small fingertip ROI used for local depth measurement.

## How to run

From the repository root, you can run this demo in three ways.

Recommended CLI command:

```bash
uv run oakvl run virtual-depth-piano
```

You can also use the demo number:

```bash
uv run oakvl run 013
```

Direct example entry point:

```bash
uv run python examples/013_virtual_depth_piano/run.py
```

Makefile shortcut:

```bash
make demo-013
```

## Controls

- `Q` or `ESC` — quit

## Expected behavior

The window shows two views side by side:

- RGB preview on the left
- colored disparity view on the right

Move your index finger over the virtual keys. A key should light up when the fingertip hovers over it. Move the fingertip closer to the camera to satisfy the depth press threshold and trigger a note.

The HUD shows:

- detected fingertip count
- depth-pressed fingertip count
- maximum local fingertip disparity
- press threshold
- audio status
- total triggered notes
- last triggered note

## Notes

This demo uses a presentation-level approximation between RGB and disparity coordinates. The RGB and stereo cameras have different viewpoints, so the fingertip-to-disparity mapping is approximate.

A larger local disparity ROI is used to make the interaction more forgiving.

If audio initialization fails, the demo continues to work visually.

## Experiment ideas

- Tune `DEFAULT_PRESS_DISPARITY_THRESHOLD`.
- Change the piano key layout.
- Add more notes.
- Enable multiple fingertips.
- Add black keys.
- Add key release animations.
- Add a recording mode for short melodies.
- Extend the demo into a laser harp or air piano interface.