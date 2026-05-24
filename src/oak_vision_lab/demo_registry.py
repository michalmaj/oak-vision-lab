"""Demo registry for oak-vision-lab."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DemoEntry:
    """Metadata required to describe and run a demo."""

    number: str
    slug: str
    title: str
    short_description: str
    run_module: str
    run_function: str
    example_path: str
    readme_en: str
    readme_pl: str


DEMOS: tuple[DemoEntry, ...] = (
    DemoEntry(
        number="001",
        slug="camera-preview-hud",
        title="Camera Preview HUD",
        short_description="Real-time RGB camera preview with HUD.",
        run_module="oak_vision_lab.demos.camera_preview_hud",
        run_function="run_camera_preview_hud",
        example_path="examples/001_camera_preview_hud/run.py",
        readme_en="examples/001_camera_preview_hud/README.md",
        readme_pl="examples/001_camera_preview_hud/README.pl.md",
    ),
    DemoEntry(
        number="002",
        slug="depth-map-viewer",
        title="Depth Map Viewer",
        short_description="Colorful stereo disparity visualization.",
        run_module="oak_vision_lab.demos.depth_map_viewer",
        run_function="run_depth_map_viewer",
        example_path="examples/002_depth_map_viewer/run.py",
        readme_en="examples/002_depth_map_viewer/README.md",
        readme_pl="examples/002_depth_map_viewer/README.pl.md",
    ),
    DemoEntry(
        number="003",
        slug="rgb-depth-split-screen",
        title="RGB + Depth Split-Screen",
        short_description="Side-by-side RGB and disparity preview.",
        run_module="oak_vision_lab.demos.rgb_depth_split_screen",
        run_function="run_rgb_depth_split_screen",
        example_path="examples/003_rgb_depth_split_screen/run.py",
        readme_en="examples/003_rgb_depth_split_screen/README.md",
        readme_pl="examples/003_rgb_depth_split_screen/README.pl.md",
    ),
    DemoEntry(
        number="004",
        slug="depth-proximity-alert",
        title="Depth Proximity Alert",
        short_description="Visual alert when an object gets close to the center.",
        run_module="oak_vision_lab.demos.depth_proximity_alert",
        run_function="run_depth_proximity_alert",
        example_path="examples/004_depth_proximity_alert/run.py",
        readme_en="examples/004_depth_proximity_alert/README.md",
        readme_pl="examples/004_depth_proximity_alert/README.pl.md",
    ),
    DemoEntry(
        number="005",
        slug="depth-hot-zone-game",
        title="Depth Hot Zone Game",
        short_description="Score points by reaching a central depth-based hot zone.",
        run_module="oak_vision_lab.demos.depth_hot_zone_game",
        run_function="run_depth_hot_zone_game",
        example_path="examples/005_depth_hot_zone_game/run.py",
        readme_en="examples/005_depth_hot_zone_game/README.md",
        readme_pl="examples/005_depth_hot_zone_game/README.pl.md",
    ),
    DemoEntry(
        number="006",
        slug="moving-depth-target-game",
        title="Moving Depth Target Game",
        short_description="Score points by reaching moving depth-based targets.",
        run_module="oak_vision_lab.demos.moving_depth_target_game",
        run_function="run_moving_depth_target_game",
        example_path="examples/006_moving_depth_target_game/run.py",
        readme_en="examples/006_moving_depth_target_game/README.md",
        readme_pl="examples/006_moving_depth_target_game/README.pl.md",
    ),
    DemoEntry(
        number="007",
        slug="multi-zone-reaction-game",
        title="Multi-Zone Reaction Game",
        short_description="Reaction game with multiple depth-based zones.",
        run_module="oak_vision_lab.demos.multi_zone_reaction_game",
        run_function="run_multi_zone_reaction_game",
        example_path="examples/007_multi_zone_reaction_game/run.py",
        readme_en="examples/007_multi_zone_reaction_game/README.md",
        readme_pl="examples/007_multi_zone_reaction_game/README.pl.md",
    ),
    DemoEntry(
        number="008",
        slug="reaction-time-game",
        title="Reaction Time Game",
        short_description="Measure reaction time using a depth-based target zone.",
        run_module="oak_vision_lab.demos.reaction_time_game",
        run_function="run",
        example_path="examples/008_reaction_time_game/run.py",
        readme_en="examples/008_reaction_time_game/README.md",
        readme_pl="examples/008_reaction_time_game/README.pl.md",
    ),
    DemoEntry(
        number="009",
        slug="object-distance-meter",
        title="Object Distance Meter",
        short_description="Measure object proximity using \
RGB preview and stereo disparity.",
        run_module="oak_vision_lab.demos.object_distance_meter",
        run_function="run",
        example_path="examples/009_object_distance_meter/run.py",
        readme_en="examples/009_object_distance_meter/README.md",
        readme_pl="examples/009_object_distance_meter/README.pl.md",
    ),
    DemoEntry(
        number="010",
        slug="closest-object-tracker",
        title="Closest Object Tracker",
        short_description="Track the closest region using \
RGB preview and stereo disparity.",
        run_module="oak_vision_lab.demos.closest_object_tracker",
        run_function="run",
        example_path="examples/010_closest_object_tracker/run.py",
        readme_en="examples/010_closest_object_tracker/README.md",
        readme_pl="examples/010_closest_object_tracker/README.pl.md",
    ),
    DemoEntry(
        number="011",
        slug="depth-music-playground",
        title="Depth Music Playground",
        short_description="Trigger visual music zones using \
RGB preview and stereo disparity.",
        run_module="oak_vision_lab.demos.depth_music_playground",
        run_function="run",
        example_path="examples/011_depth_music_playground/run.py",
        readme_en="examples/011_depth_music_playground/README.md",
        readme_pl="examples/011_depth_music_playground/README.pl.md",
    ),
    DemoEntry(
        number="012",
        slug="depth-dodge-avoider-game",
        title="Depth Dodge / Avoider Game",
        short_description="Avoid depth-based danger zones using \
RGB preview and stereo disparity.",
        run_module="oak_vision_lab.demos.depth_dodge_avoider_game",
        run_function="run",
        example_path="examples/012_depth_dodge_avoider_game/run.py",
        readme_en="examples/012_depth_dodge_avoider_game/README.md",
        readme_pl="examples/012_depth_dodge_avoider_game/README.pl.md",
    ),
)


def list_demos() -> tuple[DemoEntry, ...]:
    """Return all registered demos."""

    return DEMOS


def resolve_demo(query: str) -> DemoEntry:
    """Resolve a demo by number or slug."""

    normalized_query = query.strip().lower()

    for demo in DEMOS:
        if normalized_query in {demo.number, demo.slug}:
            return demo

    available = ", ".join(f"{demo.number}/{demo.slug}" for demo in DEMOS)
    msg = f"Unknown demo '{query}'. Available demos: {available}"
    raise ValueError(msg)
