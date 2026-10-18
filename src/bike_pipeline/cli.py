import argparse
from collections.abc import Sequence
from pathlib import Path

from helpers import add_date_arguments
from settings import load_config
from storage import get_bike_raw_counters_path, get_bike_raw_counts_path

from .backfill import backfill_bike
from .warehouse import load_bike_range

COMMANDS = ("backfill", "warehouse", "pipeline")


def _add_source_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--counts-file",
        type=Path,
        help="Bike counts CSV (default: configured bike raw directory)",
    )
    parser.add_argument(
        "--counters-file",
        type=Path,
        help="Bike counter metadata CSV (default: configured bike raw directory)",
    )


def build_parser() -> argparse.ArgumentParser:
    """Build the bike pipeline command-line argument parser."""
    parser = argparse.ArgumentParser(description="Bike Data Pipeline CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    descriptions = {
        "backfill": "Read CSV data and write Bronze/Silver Parquet files",
        "warehouse": "Load existing Silver Parquet files into PostgreSQL",
        "pipeline": "Run CSV ingestion, transformations, and database loading",
    }
    for command in COMMANDS:
        command_parser = subparsers.add_parser(
            command,
            help=descriptions[command],
        )
        add_date_arguments(command_parser)
        if command in {"backfill", "pipeline"}:
            _add_source_arguments(command_parser)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the selected bike pipeline stage."""
    args = build_parser().parse_args(argv)
    config = load_config()

    if args.command in {"backfill", "pipeline"}:
        counts_file_path = args.counts_file or get_bike_raw_counts_path(config)
        counters_file_path = (
            args.counters_file or get_bike_raw_counters_path(config)
        )
        backfill_bike(
            config=config,
            counts_file_path=counts_file_path,
            counters_file_path=counters_file_path,
            start_date=args.start_date,
            end_date=args.end_date,
        )

    if args.command in {"warehouse", "pipeline"}:
        load_bike_range(
            config=config,
            start_date=args.start_date,
            end_date=args.end_date,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
