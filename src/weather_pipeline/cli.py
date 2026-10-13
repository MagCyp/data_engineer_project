import argparse
from collections.abc import Sequence
from typing import Any

from helpers import parse_date
from settings import load_config

from .backfill import backfill_weather
from .warehouse import load_weather_range

COMMANDS = ("backfill", "warehouse", "pipeline")


def _add_common_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--location",
        help="Location to process (uses default_city when omitted)",
    )
    parser.add_argument(
        "--start-date",
        type=parse_date,
        required=True,
        help="First date to process (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--end-date",
        type=parse_date,
        required=True,
        help="Last date to process (YYYY-MM-DD)",
    )


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(description="Weather Data Pipeline CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    descriptions = {
        "backfill": "Download API data and write Bronze/Silver Parquet files",
        "warehouse": "Load existing Silver Parquet files into PostgreSQL",
        "pipeline": "Run API ingestion, transformations, and database loading",
    }
    for command in COMMANDS:
        command_parser = subparsers.add_parser(
            command,
            help=descriptions[command],
        )
        _add_common_arguments(command_parser)

    return parser


def _selected_location(config: dict[str, Any], location: str | None) -> str:
    return str(config["default_city"]) if location is None else location


def main(argv: Sequence[str] | None = None) -> int:
    """Run the weather backfill CLI."""
    args = build_parser().parse_args(argv)
    config = load_config()
    location = _selected_location(config, args.location)

    if args.command in {"backfill", "pipeline"}:
        backfill_weather(
            config=config,
            location=location,
            start_date=args.start_date,
            end_date=args.end_date,
        )

    if args.command in {"warehouse", "pipeline"}:
        load_weather_range(
            config=config,
            location=location,
            start_date=args.start_date,
            end_date=args.end_date,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
