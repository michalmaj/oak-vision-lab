# 009 — Object Distance Meter

Object Distance Meter is an interactive OAK-D demo that combines an RGB camera preview with stereo disparity measurement.

The RGB view is used as the main presentation layer and HUD, while the colored disparity view is shown next to it as the measurement/debug layer. The demo measures mean disparity inside a central region of interest and turns it into a simple proximity meter.

## What it demonstrates

- RGB preview as a user-facing HUD
- Stereo disparity as a measurement layer
- Split-screen multimodal presentation
- Region-of-interest disparity analysis
- Depth-based proximity classification
- Live proximity meter visualization
- Simple statistics: sample count, min/max disparity and peak proximity level

## How to run

From the repository root, you can run this demo in three ways.

Recommended CLI command:

```bash
uv run oakvl run object-distance-meter
```

You can also use the demo number:

```bash
uv run oakvl run 009
```

Direct example entry point:

```bash
uv run python examples/009_object_distance_meter/run.py
```

Makefile shortcut:

```bash
make demo-009
```

## Controls

- `R` — reset statistics
- `Q` or `ESC` — quit

## Expected behavior

The window shows two views side by side:

- RGB preview on the left
- colored disparity view on the right

A central region of interest is drawn on both views. The measurement is computed from the disparity view, while the result is displayed on the RGB HUD.

Move a hand, notebook, bottle or another object toward the camera. The proximity meter should increase as the object gets closer.

The HUD shows:

- mean disparity
- proximity level
- sample count
- minimum and maximum observed disparity
- peak proximity level
- a short proximity message

## Notes

This demo uses disparity as a relative proximity signal, not a calibrated metric distance in centimeters or meters.

The RGB and stereo cameras have different viewpoints, so the regions shown on RGB and disparity are intentionally treated as a presentation-level approximation. A later demo may use RGB-aligned depth or spatial coordinates for more precise metric measurement.

## Experiment ideas

- Move different objects into the region of interest.
- Compare how hands, notebooks, bottles and larger objects affect mean disparity.
- Change the region size.
- Tune the `near` and `very close` thresholds.
- Try using only the RGB view as a presentation HUD.
- Extend the demo into a calibrated 3D measuring tape.