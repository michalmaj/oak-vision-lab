# 008 — Reaction Time Game

Reaction Time Game is an interactive OAK-D demo that measures how quickly a user reacts to a depth-based target zone.

The demo displays a central target region on top of a colored stereo disparity view. The player has to wait until the target becomes active and then move a hand or object close to the camera as quickly as possible.

## What it demonstrates

- Stereo disparity visualization
- Depth-based interaction
- Region-of-interest analysis
- Reaction time measurement
- Game state management
- Testable game logic separated from camera input

## How to run

From the repository root, you can run this demo in three ways.

Recommended CLI command:

```bash
uv run oakvl run reaction-time-game
```

You can also use the demo number:

```bash
uv run oakvl run 008
```

Direct example entry point:

```bash
uv run python examples/008_reaction_time_game/run.py
```

Makefile shortcut:

```bash
make demo-008
```

## Controls

- `R` — restart the game
- `Q` or `ESC` — quit

## Expected behavior

The game starts with a short random waiting period. When the target changes to `HIT NOW!`, move a hand or object into the highlighted region and close to the camera.

The HUD shows:

- remaining time
- score
- current phase
- last reaction time
- best reaction time
- average reaction time
- mean disparity in the target region
- proximity level

## Experiment ideas

- Try reacting with your hand, a notebook, or another object.
- Change the target region size.
- Adjust the proximity threshold.
- Add penalties for moving too early.
- Add sound effects for hits and game over.