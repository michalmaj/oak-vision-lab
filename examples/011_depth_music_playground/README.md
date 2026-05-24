# 011 — Depth Music Playground

Depth Music Playground is an interactive OAK-D demo that turns depth-based zones into a visual musical instrument.

The RGB view is used as the main presentation layer and HUD, while the colored disparity view is shown next to it as the measurement/debug layer. Moving a hand or object into one of the zones triggers a visual note event.

## What it demonstrates

- RGB preview as a user-facing HUD
- Stereo disparity as a measurement layer
- Split-screen multimodal presentation
- Depth-based interaction zones
- Region-of-interest disparity analysis
- Visual note triggers
- Per-zone cooldown logic
- Testable interaction logic separated from camera input

## How it works

The frame is divided into horizontal music zones, each mapped to a note:

```text
C  D  E  G  A
```

For each zone, the demo computes the mean non-zero disparity. If the zone becomes `NEAR` or `VERY_CLOSE`, it becomes active and can trigger a note event. Each zone has a short cooldown to prevent continuous triggering every frame.

The current version provides visual note triggers and optional pygame-based audio output. If audio initialization fails, the demo continues to work visually.

## How to run

From the repository root, you can run this demo in three ways.

Recommended CLI command:

```bash
uv run oakvl run depth-music-playground
```

You can also use the demo number:

```bash
uv run oakvl run 011
```

Direct example entry point:

```bash
uv run python examples/011_depth_music_playground/run.py
```

Makefile shortcut:

```bash
make demo-011
```

## Controls

- `R` — reset state
- `Q` or `ESC` — quit

## Expected behavior

The window shows two views side by side:

- RGB preview on the left
- colored disparity view on the right
- When audio is available, each triggered zone also plays a short note.

Five music zones are drawn across both views. Move a hand, notebook, bottle or another object into a zone and closer to the camera. The active zone should light up and trigger a visual note event.

The HUD shows:

- total trigger count
- last triggered note
- current music message
- controls

## Notes

This demo uses disparity as a relative proximity signal, not a calibrated metric distance.

The RGB and stereo cameras have different viewpoints, so the zones shown on RGB and disparity are treated as a presentation-level approximation. This is sufficient for an interactive visual instrument, but not intended as precise metric tracking.

## Experiment ideas

- Change the note sequence.
- Add more or fewer zones.
- Tune the trigger cooldown.
- Add audio output for each note.
- Add different visual effects for each note.
- Turn the demo into a laser harp-style interaction.
- Add a recording mode that stores a short sequence of triggered notes.