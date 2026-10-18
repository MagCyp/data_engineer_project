from datetime import UTC, datetime
from typing import Annotated

import polars as pl
from pydantic import AfterValidator, Field, StringConstraints


def ensure_naive_datetime(value: datetime) -> datetime:
    if value.tzinfo is not None and value.utcoffset() is not None:
        raise ValueError("local timestamps must not contain a timezone")
    return value


def normalize_utc_datetime(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("UTC timestamps must be timezone-aware")
    return value.astimezone(UTC)


def require_dataframe_schema(
    dataframe: pl.DataFrame,
    schema: pl.Schema,
    *,
    name: str,
) -> None:
    """Require all columns and dtypes declared by a Polars schema."""
    missing_columns = set(schema.names()).difference(dataframe.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Missing {name} columns: {missing}")

    for column, expected_dtype in schema.items():
        if dataframe.schema[column] != expected_dtype:
            raise ValueError(
                f"{name} column '{column}' must use {expected_dtype}"
            )


def require_valid_rows(
    dataframe: pl.DataFrame,
    valid_row: pl.Expr,
    *,
    name: str,
) -> None:
    """Raise when any DataFrame row fails the supplied predicate."""
    invalid_count = dataframe.select((~valid_row.fill_null(False)).sum()).item()
    if invalid_count:
        raise ValueError(f"{name} validation failed for {invalid_count} row(s)")


def require_unique_columns(
    dataframe: pl.DataFrame,
    columns: str | tuple[str, ...],
    *,
    message: str,
) -> None:
    """Raise when a column or composite key contains duplicates."""
    selected_columns = (columns,) if isinstance(columns, str) else columns
    if dataframe.select(selected_columns).is_duplicated().any():
        raise ValueError(message)


def non_empty_strings(columns: tuple[str, ...]) -> pl.Expr:
    """Build a predicate requiring non-null, non-blank string columns."""
    return pl.all_horizontal(
        pl.col(column).str.strip_chars().str.len_chars() > 0
        for column in columns
    )


def finite_non_negative_numbers(columns: tuple[str, ...]) -> pl.Expr:
    """Build a predicate requiring finite, non-negative numeric columns."""
    return pl.all_horizontal(
        pl.col(column).is_finite() & (pl.col(column) >= 0)
        for column in columns
    )


Latitude = Annotated[float, Field(ge=-90, le=90)]
Longitude = Annotated[float, Field(ge=-180, le=180)]
NaiveDateTime = Annotated[datetime, AfterValidator(ensure_naive_datetime)]
NonEmptyString = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1),
]
NonNegativeFloat = Annotated[float, Field(ge=0)]
NonNegativeInt = Annotated[int, Field(ge=0)]
Percentage = Annotated[int, Field(ge=0, le=100)]
PositiveInt = Annotated[int, Field(gt=0)]
UTCDateTime = Annotated[datetime, AfterValidator(normalize_utc_datetime)]
