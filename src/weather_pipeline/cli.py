import argparse
from collections.abc import Sequence

from backfill import backfill_weather
from helpers import parse_date
from settings import load_config


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(description="Weather Data Pipeline CLI")
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
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the weather backfill CLI."""
    args = build_parser().parse_args(argv)
    config = load_config()

    backfill_weather(
        config=config,
        location=args.location,
        start_date=args.start_date,
        end_date=args.end_date,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
