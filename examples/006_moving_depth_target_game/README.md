# Moving Depth Target Game

> A real-time depth-based mini-game where the player scores points by reaching moving target zones.

This demo extends the idea of a fixed depth hot zone into a more dynamic game.

Instead of using one static region in the center of the image, the active target appears in different places. The player scores points by moving a hand or object close enough to the current target zone.

## What it does

The application:

- creates a stereo disparity pipeline,
- visualizes disparity with an OpenCV colormap,
- generates a target zone at a random position,
- extracts disparity data from the current target region,
- computes mean disparity inside the target,
- classifies proximity into simple levels,
- awards points when the player reaches the active target,
- moves the target after a successful hit,
- displays score and time left,
- supports restart and basic keyboard interaction.

## Why it is useful

This demo shows how computer vision can be used to create a simple interactive game.

Compared with a fixed hot zone, the moving target makes the interaction more engaging. The player has to react, move, and aim at the current target location.

It is useful for teaching because it connects:

- perception,
- random target generation,
- region-of-interest processing,
- real-time decision logic,
- stateful game mechanics,
- visual feedback.

It is also more fun during live demonstrations because people can compete for a higher score.

## What you will learn

This demo introduces:

- moving target zones,
- normalized target coordinates,
- target ROI extraction,
- disparity-based hit detection,
- score and timer logic,
- target relocation after scoring,
- cooldown-based scoring,
- separating pure game logic from camera-dependent code.

## How it works

The game stores the active target as normalized coordinates:

```text
TargetZone(center_x, center_y, scale)
```

For each frame:

1. The disparity frame is captured.
2. The current target zone is converted into pixel coordinates.
3. The target region is extracted from the disparity frame.
4. Mean disparity is computed inside the target.
5. The result is classified as `SAFE`, `NEAR`, or `VERY CLOSE`.
6. If the object is close enough and the cooldown has passed, points are awarded.
7. After a hit, the target moves to a new random position.

The player tries to hit as many target zones as possible before the timer ends.

## How to run

From the repository root, you can run this demo in three ways.

Recommended CLI command:

```bash
uv run oakvl run moving-depth-target-game
```

You can also use the demo number:

```bash
uv run oakvl run 006
```

Direct example entry point:

```bash
uv run python examples/006_moving_depth_target_game/run.py
```

Makefile shortcut:

```bash
make demo-006
```

## Controls

```text
q  - quit the demo
h  - show/hide help text
r  - restart the game
```

## Expected result

A colorful disparity visualization should appear.

A visible target zone should be displayed somewhere in the frame.

When a hand or object moves close enough into the current target:

- the score should increase,
- the target should move to a new position,
- the alert color should change,
- the game panel should show a hit message.

After the timer finishes, the HUD should display the final score.

## Ideas for experiments

Try modifying:

- game duration,
- target size,
- target position range,
- points per hit,
- hit cooldown,
- proximity thresholds,
- alert colors,
- scoring rules.

Possible extensions:

- add difficulty levels,
- shrink the target over time,
- increase target speed after each hit,
- add sound effects,
- add a high-score table,
- add a start screen,
- add a countdown before the game starts,
- add bonus targets,
- add penalty zones.