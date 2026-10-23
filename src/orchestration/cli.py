import argparse
import os
from collections.abc import Sequence

from dotenv import load_dotenv

from helpers import add_date_arguments
from settings import load_config

from .date_range_validation import validate_mobility_date_range

SOCRATA_APP_TOKEN_ENV = "SOCRATA_APP_TOKEN"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Project orchestration CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate_parser = subparsers.add_parser(
        "validate-range",
        help="Validate a date range against all source boundaries",
    )
    add_date_arguments(validate_parser)
    return parser


def _get_socrata_app_token() -> str | None:
    value = os.getenv(SOCRATA_APP_TOKEN_ENV)
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    load_dotenv()
    if args.command == "validate-range":
        latest_common_date = validate_mobility_date_range(
            load_config(),
            start_date=args.start_date,
            end_date=args.end_date,
            app_token=_get_socrata_app_token(),
        )
        print(
            f"Validated {args.start_date} through {args.end_date}; "
            f"latest common source date is {latest_common_date}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
