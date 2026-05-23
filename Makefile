.PHONY: sync format lint test check \
	demo-001 demo-002 demo-003 demo-004 demo-005 demo-006 demo-007 demo-008 \
	demo-009 \
	demos help \
	cli-list cli-info-001 cli-info-007 \
	doctor \
	doctor-device

sync:
	uv sync

format:
	uv run ruff format .

lint:
	uv run ruff check .

test:
	uv run pytest

check:
	uv run ruff format --check .
	uv run ruff check .
	uv run pytest

demo-001:
	uv run python examples/001_camera_preview_hud/run.py

demo-002:
	uv run python examples/002_depth_map_viewer/run.py

demo-003:
	uv run python examples/003_rgb_depth_split_screen/run.py

demo-004:
	uv run python examples/004_depth_proximity_alert/run.py

demo-005:
	uv run python examples/005_depth_hot_zone_game/run.py

demo-006:
	uv run python examples/006_moving_depth_target_game/run.py

demo-007:
	uv run python examples/007_multi_zone_reaction_game/run.py

demo-008:
	uv run python examples/008_reaction_time_game/run.py

demo-009:
	uv run python examples/009_object_distance_meter/run.py

cli-list:
	uv run oakvl list

cli-info-001:
	uv run oakvl info 001

cli-info-007:
	uv run oakvl info 007

doctor:
	uv run oakvl doctor

doctor-device:
	uv run oakvl doctor --device

demos:
	@echo "Available demos:"
	@echo "  make demo-001  Camera Preview HUD"
	@echo "  make demo-002  Depth Map Viewer"
	@echo "  make demo-003  RGB + Depth Split-Screen"
	@echo "  make demo-004  Depth Proximity Alert"
	@echo "  make demo-005  Depth Hot Zone Game"
	@echo "  make demo-006  Moving Depth Target Game"
	@echo "  make demo-007  Multi-Zone Reaction Game"

help:
	@echo "oak-vision-lab Makefile shortcuts"
	@echo ""
	@echo "Development:"
	@echo "  make sync      Install/sync dependencies"
	@echo "  make format    Format code with Ruff"
	@echo "  make lint      Run Ruff lint checks"
	@echo "  make test      Run pytest"
	@echo "  make check     Run formatting check, lint and tests"
	@echo ""
	@echo "Demos:"
	@echo "  make demos     List available demos"
	@echo "  make demo-001  Run Camera Preview HUD"
	@echo "  make demo-002  Run Depth Map Viewer"
	@echo "  make demo-003  Run RGB + Depth Split-Screen"
	@echo "  make demo-004  Run Depth Proximity Alert"
	@echo "  make demo-005  Run Depth Hot Zone Game"
	@echo "  make demo-006  Run Moving Depth Target Game"
	@echo "  make demo-007  Run Multi-Zone Reaction Game"
	@echo "  make demo-008  Run Reaction Time Game"
	@echo "  make demo-009  Run Object Distance Meter"
	@echo ""
	@echo "CLI:"
	@echo "  make cli-list      List demos using the oakvl CLI"
	@echo "  make cli-info-001  Show CLI info for demo 001"
	@echo "  make cli-info-007  Show CLI info for demo 007"
	@echo "  make doctor        Run software environment diagnostics"
	@echo "  make doctor-device Run diagnostics including OAK-D device discovery"