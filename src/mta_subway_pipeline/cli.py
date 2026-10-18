import argparse
import os
from collections.abc import Sequence

from dotenv import load_dotenv

from helpers import add_date_arguments
from settings import load_config

from .backfill import backfill_subway
from .ingestion import SOCRATA_MAX_PAGE_SIZE
from .warehouse import load_subway_range

COMMANDS = ("backfill", "warehouse", "pipeline")
SOCRATA_APP_TOKEN_ENV = "SOCRATA_APP_TOKEN"


def build_parser() -> argparse.ArgumentParser:
    """Build the subway pipeline command-line argument parser."""
    parser = argparse.ArgumentParser(description="MTA Subway Pipeline CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    descriptions = {
        "backfill": "Download API data and write Bronze/Silver Parquet files",
        "warehouse": "Load existing Silver Parquet files into PostgreSQL",
        "pipeline": "Run ingestion, transformations, and database loading",
    }
    for command in COMMANDS:
        command_parser = subparsers.add_parser(
            command,
            help=descriptions[command],
        )
        add_date_arguments(command_parser)
        if command in {"backfill", "pipeline"}:
            command_parser.add_argument(
                "--page-size",
                type=int,
                default=SOCRATA_MAX_PAGE_SIZE,
                help="Rows requested per Socrata page",
            )

    return parser


def _get_socrata_app_token() -> str | None:
    app_token = os.getenv(SOCRATA_APP_TOKEN_ENV)
    if app_token is None:
        return None
    normalized_token = app_token.strip()
    return normalized_token or None


def main(argv: Sequence[str] | None = None) -> int:
    """Run the selected subway pipeline stage."""
    args = build_parser().parse_args(argv)
    load_dotenv()
    config = load_config()

    if args.command in {"backfill", "pipeline"}:
        app_token = _get_socrata_app_token()
        backfill_subway(
            config=config,
            start_date=args.start_date,
            end_date=args.end_date,
            page_size=args.page_size,
            app_token=app_token,
        )

    if args.command in {"warehouse", "pipeline"}:
        load_subway_range(
            config=config,
            start_date=args.start_date,
            end_date=args.end_date,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
