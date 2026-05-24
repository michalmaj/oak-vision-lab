# 012 — Depth Dodge / Avoider Game

Depth Dodge / Avoider Game is an interactive OAK-D mini-game where the player must avoid depth-based danger zones.

The RGB view is used as the main game HUD, while the colored disparity view is shown next to it as the measurement/debug layer. One zone is highlighted as the current danger zone. The player scores points by keeping a hand or object away from that zone until it changes.

## What it demonstrates

- RGB preview as a user-facing game HUD
- Stereo disparity as a measurement layer
- Split-screen multimodal presentation
- Depth-based interaction zones
- Danger-zone collision detection
- Lives, score and collision tracking
- Timed zone switching
- Testable game logic separated from camera input

## How it works

The frame is divided into four vertical zones. One zone is selected as the active danger zone.

For each zone, the demo computes the mean non-zero disparity. If the active danger zone becomes `NEAR` or `VERY_CLOSE`, the game registers a collision and the player loses one life.

If the player survives until the danger zone changes, the score increases.

## How to run

From the repository root, you can run this demo in three ways.

Recommended CLI command:

```bash
uv run oakvl run depth-dodge-avoider-game
```

You can also use the demo number:

```bash
uv run oakvl run 012
```

Direct example entry point:

```bash
uv run python examples/012_depth_dodge_avoider_game/run.py
```

Makefile shortcut:

```bash
make demo-012
```

## Controls

- `R` — restart the game
- `Q` or `ESC` — quit

## Expected behavior

The window shows two views side by side:

- RGB preview on the left
- colored disparity view on the right

Four zones are drawn across both views. One zone is highlighted as `DANGER`. Move a hand, notebook, bottle or another object into the non-danger zones and avoid the highlighted danger zone.

The HUD shows:

- score
- remaining lives
- collision count
- active zone
- time until the next zone change
- current game message
- controls

## Notes

This demo uses disparity as a relative proximity signal, not a calibrated metric distance.

The RGB and stereo cameras have different viewpoints, so the zones shown on RGB and disparity are treated as a presentation-level approximation. This is sufficient for an interactive game mechanic, but not intended as precise metric tracking.

## Experiment ideas

- Change the number of zones.
- Adjust the zone switching speed.
- Tune the collision cooldown.
- Increase the difficulty over time.
- Add sound effects for score, collision and game over.
- Add a high-score table.
- Turn the game into a full body-based dodge game using pose estimation.