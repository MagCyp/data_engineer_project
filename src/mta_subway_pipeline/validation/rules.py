import polars as pl

from common.validation import finite_non_negative_numbers, non_empty_strings

from .models import SUBWAY_STRING_COLUMNS


def valid_subway_values() -> pl.Expr:
    """Return the shared row rules for subway dimensions and measures."""
    return (
        non_empty_strings(SUBWAY_STRING_COLUMNS)
        & finite_non_negative_numbers(("ridership",))
        & pl.col("transfers").is_finite()
        & (pl.col("transfers") <= pl.col("ridership"))
        & pl.col("latitude").is_finite()
        & pl.col("latitude").is_between(-90, 90, closed="both")
        & pl.col("longitude").is_finite()
        & pl.col("longitude").is_between(-180, 180, closed="both")
    )
