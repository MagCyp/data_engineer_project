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
