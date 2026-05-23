# 010 — Closest Object Tracker

Closest Object Tracker is an interactive OAK-D demo that searches for the closest region in a stereo disparity image and presents the result on an RGB camera HUD.

The RGB view is used as the main user-facing layer, while the colored disparity view shows the measurement/debug layer with a tracking grid.

## What it demonstrates

- RGB preview as a user-facing HUD
- Stereo disparity as a measurement layer
- Split-screen multimodal presentation
- Grid-based disparity analysis
- Closest-region selection
- Proximity classification
- Region scaling between disparity and RGB views
- Simple tracker statistics

## How it works

The disparity frame is divided into a regular grid. For each cell, the demo computes the mean non-zero disparity. The cell with the highest mean disparity is treated as the region most likely to contain the closest visible object.

The selected region is highlighted on the disparity view and scaled to the RGB view for presentation.

## How to run

From the repository root, you can run this demo in three ways.

Recommended CLI command:

```bash
uv run oakvl run closest-object-tracker
```

You can also use the demo number:

```bash
uv run oakvl run 010
```

Direct example entry point:

```bash
uv run python examples/010_closest_object_tracker/run.py
```

Makefile shortcut:

```bash
make demo-010
```

## Controls

- `R` — reset statistics
- `Q` or `ESC` — quit

## Expected behavior

The window shows two views side by side:

- RGB preview on the left
- colored disparity view on the right

A subtle grid is drawn on the disparity view. The region with the highest mean disparity is highlighted as the closest detected region. The corresponding scaled region is also drawn on the RGB HUD.

Move a hand, notebook, bottle or another object closer to the camera. The highlighted region should move toward the grid cell where the closest object appears.

The HUD shows:

- detection status
- mean disparity of the selected region
- proximity level
- processed frame count
- detection count
- detection ratio
- maximum observed disparity
- peak proximity level
- a short tracker message

## Notes

This demo uses a simple grid-based tracker. It does not perform semantic object detection and does not know what the object is. It only estimates which grid region has the strongest disparity response.

The RGB and stereo cameras have different viewpoints, so the region drawn on RGB is an approximate presentation overlay based on scaling from the disparity frame. A later demo may use RGB-aligned depth or spatial coordinates for more precise tracking.

## Experiment ideas

- Move objects across different parts of the frame.
- Change the grid size from `3 x 4` to a finer layout.
- Increase `DEFAULT_MIN_MEAN_DISPARITY` to reduce false detections.
- Compare how small and large objects affect the selected region.
- Add smoothing so the highlighted region changes less abruptly.
- Extend the tracker into a particle effect or game mechanic.