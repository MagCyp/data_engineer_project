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
