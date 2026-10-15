import argparse
from collections.abc import Sequence
from pathlib import Path

from helpers import parse_date
from settings import load_config

from .backfill import backfill_bike
from .warehouse import load_bike_range

COMMANDS = ("backfill", "warehouse", "pipeline")
DEFAULT_COUNTS_FILE = Path("data/raw/bicycle_counts.csv")
DEFAULT_COUNTERS_FILE = Path("data/raw/bicycle_counters.csv")


def _add_date_arguments(parser: argparse.ArgumentParser) -> None:
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


def _add_source_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--counts-file",
        type=Path,
        default=DEFAULT_COUNTS_FILE,
        help=f"Bike counts CSV (default: {DEFAULT_COUNTS_FILE})",
    )
    parser.add_argument(
        "--counters-file",
        type=Path,
        default=DEFAULT_COUNTERS_FILE,
        help=f"Bike counter metadata CSV (default: {DEFAULT_COUNTERS_FILE})",
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
        _add_date_arguments(command_parser)
        if command in {"backfill", "pipeline"}:
            _add_source_arguments(command_parser)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the selected bike pipeline stage."""
    args = build_parser().parse_args(argv)
    config = load_config()

    if args.command in {"backfill", "pipeline"}:
        backfill_bike(
            config=config,
            counts_file_path=args.counts_file,
            counters_file_path=args.counters_file,
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
