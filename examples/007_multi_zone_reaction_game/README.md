# Multi-Zone Reaction Game

> A real-time depth-based reaction game where the player scores points by reaching the currently active zone.

This demo turns stereo disparity into a simple arcade-style reaction game.

Several zones are displayed on the screen, but only one of them is active at a time. The player has to move a hand or object close enough to the active zone. After a successful hit, another zone becomes active.

## What it does

The application:

- creates a stereo disparity pipeline,
- visualizes disparity with an OpenCV colormap,
- displays multiple reaction zones,
- highlights the currently active zone,
- extracts disparity data from the active zone,
- computes mean disparity inside that zone,
- classifies proximity into simple levels,
- awards points when the player reaches the active zone,
- changes the active zone after a successful hit,
- displays score and time left,
- supports restart and basic keyboard interaction.

## Why it is useful

This demo shows how computer vision can support fast, interactive feedback loops.

Compared with a single hot zone, multiple zones make the interaction more dynamic. The player has to react to changing targets and move toward the correct area.

It is useful for teaching because it connects:

- perception,
- region-of-interest processing,
- simple decision logic,
- game state,
- reaction-based interaction,
- real-time visual feedback.

It also works well during live demonstrations because participants can compete for a higher score.

## What you will learn

This demo introduces:

- multiple interaction zones,
- active target selection,
- zone-based ROI extraction,
- depth-like hit detection,
- reaction game mechanics,
- score and timer logic,
- cooldown-based scoring,
- use of shared depth and game utilities.

## How it works

The demo defines four reaction zones:

```text
+-------------------------+
|     A           B       |
|                         |
|                         |
|     C           D       |
+-------------------------+
```

For each frame:

1. The disparity frame is captured.
2. The currently active zone is selected.
3. The active zone is converted into pixel coordinates.
4. The zone ROI is extracted from the disparity frame.
5. Mean disparity is computed inside the active zone.
6. The result is classified as `SAFE`, `NEAR`, or `VERY CLOSE`.
7. If the object is close enough and the cooldown has passed, points are awarded.
8. After a hit, a different zone becomes active.

The player tries to hit as many active zones as possible before the timer ends.

## How to run

From the repository root, you can run this demo in three ways.

Recommended CLI command:

```bash
uv run oakvl run multi-zone-reaction-game
```

You can also use the demo number:

```bash
uv run oakvl run 007
```

Direct example entry point:

```bash
uv run python examples/007_multi_zone_reaction_game/run.py
```

Makefile shortcut:

```bash
make demo-007
```

## Controls

```text
q  - quit the demo
h  - show/hide help text
r  - restart the game
```

## Expected result

A colorful disparity visualization should appear.

Four zones should be displayed on the screen. One zone should be marked as active.

When a hand or object moves close enough into the active zone:

- the score should increase,
- another zone should become active,
- the alert color should change,
- the game panel should show a hit message.

After the timer finishes, the HUD should display the final score.

## Ideas for experiments

Try modifying:

- number of zones,
- zone positions,
- zone size,
- game duration,
- points per hit,
- hit cooldown,
- proximity thresholds,
- active zone selection rules.

Possible extensions:

- add difficulty levels,
- add shrinking zones,
- add penalty zones,
- add bonus zones,
- add sound effects,
- add a high-score table,
- add reaction time measurement,
- add a presentation mode with larger labels.