"""Command line interface for oak-vision-lab."""

from __future__ import annotations

import argparse
import importlib
from collections.abc import Sequence

from oak_vision_lab.demo_registry import DemoEntry, list_demos, resolve_demo


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""

    parser = argparse.ArgumentParser(
        prog="oakvl",
        description="OAK-D demo runner for oak-vision-lab.",
    )

    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser(
        "list",
        help="List available demos.",
    )

    info_parser = subparsers.add_parser(
        "info",
        help="Show details about a demo.",
    )
    info_parser.add_argument(
        "demo",
        help="Demo number or slug, for example: 001 or camera-preview-hud.",
    )

    run_parser = subparsers.add_parser(
        "run",
        help="Run a selected demo.",
    )
    run_parser.add_argument(
        "demo",
        help="Demo number or slug, for example: 007 or multi-zone-reaction-game.",
    )

    return parser


def format_demo_list(demos: Sequence[DemoEntry]) -> str:
    """Format demo list for terminal output."""

    lines = ["Available demos:", ""]

    for demo in demos:
        lines.append(f"{demo.number}  {demo.slug:<30} {demo.short_description}")

    return "\n".join(lines)


def format_demo_info(demo: DemoEntry) -> str:
    """Format detailed demo information for terminal output."""

    return "\n".join(
        [
            f"{demo.number} - {demo.slug}",
            "",
            "Title:",
            f"  {demo.title}",
            "",
            "Description:",
            f"  {demo.short_description}",
            "",
            "Run methods:",
            f"  uv run oakvl run {demo.number}",
            f"  uv run oakvl run {demo.slug}",
            f"  uv run python {demo.example_path}",
            f"  make demo-{demo.number}",
            "",
            "Documentation:",
            f"  {demo.readme_en}",
            f"  {demo.readme_pl}",
        ],
    )


def run_demo(demo: DemoEntry) -> None:
    """Import and run a demo entry point."""

    module = importlib.import_module(demo.run_module)
    run_function = getattr(module, demo.run_function)
    run_function()


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI."""

    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    if args.command == "list":
        print(format_demo_list(list_demos()))
        return 0

    if args.command == "info":
        try:
            demo = resolve_demo(args.demo)
        except ValueError as error:
            parser.error(str(error))

        print(format_demo_info(demo))
        return 0

    if args.command == "run":
        try:
            demo = resolve_demo(args.demo)
        except ValueError as error:
            parser.error(str(error))

        run_demo(demo)
        return 0

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
