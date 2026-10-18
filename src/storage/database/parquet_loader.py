from collections.abc import Callable
from pathlib import Path

import polars as pl
from sqlalchemy import Table

from storage.files import load_df

from .connection import get_engine
from .db_loader import upsert_dataframe

DataFrameValidator = Callable[[pl.DataFrame], pl.DataFrame]


def load_parquet_to_table(
    file_path: str | Path,
    *,
    schema: pl.Schema,
    validator: DataFrameValidator,
    table: Table,
) -> int:
    """Validate a Parquet file and upsert it into a database table."""
    dataframe = validator(load_df(file_path, schema=schema))
    engine = get_engine()

    try:
        with engine.begin() as connection:
            return upsert_dataframe(dataframe, connection, table)
    finally:
        engine.dispose()
