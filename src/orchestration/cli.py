import argparse
import os
from collections.abc import Sequence
from datetime import date

from dotenv import load_dotenv

from helpers import add_date_arguments, parse_month, parse_year
from settings import load_config

from .date_range_validation import validate_mobility_date_range
from .periods import month_range_dates, year_range_dates

SOCRATA_APP_TOKEN_ENV = "SOCRATA_APP_TOKEN"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Project orchestration CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate_parser = subparsers.add_parser(
        "validate-range",
        help="Validate a date range against all source boundaries",
    )
    add_date_arguments(validate_parser)

    validate_month_parser = subparsers.add_parser(
        "validate-month-range",
        help="Expand and validate an inclusive month range",
    )
    validate_month_parser.add_argument(
        "--start-month",
        type=parse_month,
        required=True,
        help="First month to process (YYYY-MM)",
    )
    validate_month_parser.add_argument(
        "--end-month",
        type=parse_month,
        required=True,
        help="Last month to process (YYYY-MM)",
    )

    validate_year_parser = subparsers.add_parser(
        "validate-year-range",
        help="Expand and validate an inclusive year range",
    )
    validate_year_parser.add_argument(
        "--start-year",
        type=parse_year,
        required=True,
        help="First year to process (YYYY)",
    )
    validate_year_parser.add_argument(
        "--end-year",
        type=parse_year,
        required=True,
        help="Last year to process (YYYY)",
    )
    return parser


def _get_socrata_app_token() -> str | None:
    value = os.getenv(SOCRATA_APP_TOKEN_ENV)
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def _validate_and_print(start_date: date, end_date: date) -> None:
    latest_common_date = validate_mobility_date_range(
        load_config(),
        start_date=start_date,
        end_date=end_date,
        app_token=_get_socrata_app_token(),
    )
    print(
        f"Validated {start_date} through {end_date}; "
        f"latest common source date is {latest_common_date}"
    )
    print(f"{start_date} {end_date}")


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    load_dotenv()
    if args.command == "validate-range":
        date_range = (args.start_date, args.end_date)
    elif args.command == "validate-month-range":
        date_range = month_range_dates(args.start_month, args.end_month)
    else:
        date_range = year_range_dates(args.start_year, args.end_year)

    _validate_and_print(
        start_date=date_range[0],
        end_date=date_range[1],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
