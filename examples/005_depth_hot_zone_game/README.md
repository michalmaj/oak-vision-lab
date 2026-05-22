# Depth Hot Zone Game

> A real-time mini-game where the player scores points by moving a hand or object into a depth-based hot zone.

This demo turns stereo disparity visualization into a simple interactive game.

The player has a limited amount of time to move an object into the center hot zone. When the object is close enough, the game awards points.

## What it does

The application:

- creates a stereo disparity pipeline,
- visualizes disparity with an OpenCV colormap,
- extracts a centered hot zone,
- computes mean disparity inside the hot zone,
- classifies proximity into simple levels,
- awards points when the player reaches the active zone,
- uses a cooldown to prevent scoring every frame,
- displays score and time left,
- supports restart and basic keyboard interaction.

## Why it is useful

This demo shows how computer vision can drive simple interaction and game logic.

It is useful for teaching because it connects several concepts:

- perception,
- region-of-interest processing,
- threshold-based classification,
- real-time feedback,
- stateful application logic,
- simple game mechanics.

It also works well during workshops and live demos because people can immediately interact with the system using only their hand or a small object.

## What you will learn

This demo introduces:

- depth-like interaction using stereo disparity,
- hot zone detection,
- mean disparity analysis,
- proximity-based scoring,
- cooldown-based game logic,
- countdown timers,
- HUD-based game feedback,
- separating pure game logic from camera-dependent code.

## How it works

The demo uses a centered region of interest as the active hot zone:

```text
+-------------------------+
|                         |
|         +-------+       |
|         |  HOT  |       |
|         | ZONE  |       |
|         +-------+       |
|                         |
+-------------------------+
```

For each frame:

1. The disparity frame is captured.
2. The center hot zone is extracted.
3. Mean disparity is computed inside the hot zone.
4. The result is classified as `SAFE`, `NEAR`, or `VERY CLOSE`.
5. If the object is close enough and the cooldown has passed, points are awarded.
6. The HUD displays score, time left, status, and controls.

## How to run

From the repository root, you can run this demo in three ways.

Recommended CLI command:

```bash
uv run oakvl run depth-hot-zone-game
```

You can also use the demo number:

```bash
uv run oakvl run 005
```

Direct example entry point:

```bash
uv run python examples/005_depth_hot_zone_game/run.py
```

Makefile shortcut:

```bash
make demo-005
```

## Controls

```text
q  - quit the demo
h  - show/hide help text
r  - restart the game
```

## Expected result

A colorful disparity visualization should appear.

The center of the frame should contain a visible hot zone.

When a hand or object moves close enough into the hot zone:

- the score should increase,
- the alert color should change,
- the game panel should show a hit message.

After the timer finishes, the HUD should display the final score.

## Ideas for experiments

Try modifying:

- game duration,
- points per hit,
- hit cooldown,
- hot zone size,
- proximity thresholds,
- alert colors,
- text size,
- scoring rules.

Possible extensions:

- add difficulty levels,
- add moving hot zones,
- add multiple hot zones,
- add sound effects,
- add a high-score table,
- add a start screen,
- add a countdown before the game starts,
- add a multiplayer mode with left and right zones.