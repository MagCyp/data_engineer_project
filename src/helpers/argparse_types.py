import argparse
from datetime import date


def parse_date(value: str) -> date:
    """Parse a strict ISO date for an argparse option."""
    try:
        parsed_date = date.fromisoformat(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError(
            f"Invalid date '{value}'. Expected YYYY-MM-DD."
        ) from error

    if parsed_date.isoformat() != value:
        raise argparse.ArgumentTypeError(
            f"Invalid date '{value}'. Expected YYYY-MM-DD."
        )

    return parsed_date


def parse_month(value: str) -> date:
    """Parse a strict YYYY-MM value as the first day of that month."""
    try:
        parsed_month = date.fromisoformat(f"{value}-01")
    except ValueError as error:
        raise argparse.ArgumentTypeError(
            f"Invalid month '{value}'. Expected YYYY-MM."
        ) from error

    if parsed_month.strftime("%Y-%m") != value:
        raise argparse.ArgumentTypeError(
            f"Invalid month '{value}'. Expected YYYY-MM."
        )

    return parsed_month


def parse_year(value: str) -> int:
    """Parse a strict four-digit year."""
    if len(value) != 4 or not value.isascii() or not value.isdigit():
        raise argparse.ArgumentTypeError(
            f"Invalid year '{value}'. Expected YYYY."
        )

    parsed_year = int(value)
    if not 1 <= parsed_year <= 9999:
        raise argparse.ArgumentTypeError(
            f"Invalid year '{value}'. Expected YYYY."
        )

    return parsed_year


def add_date_arguments(parser: argparse.ArgumentParser) -> None:
    """Add the shared inclusive date-range options to a CLI parser."""
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
