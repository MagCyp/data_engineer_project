from pathlib import Path
from typing import Any

import polars as pl


def load_df(
    file_path: str | Path,
    schema: pl.Schema | dict[str, Any] | None = None,
) -> pl.DataFrame:
    """Load a Parquet file and optionally validate its exact schema."""
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"The file {path} does not exist.")

    try:
        dataframe = pl.read_parquet(path)
    except (OSError, pl.exceptions.PolarsError) as error:
        raise RuntimeError(f"Failed to load DataFrame from {path}") from error

    if schema is not None:
        expected_schema = pl.Schema(schema)
        if dataframe.schema != expected_schema:
            raise ValueError(
                "The DataFrame schema does not match the expected schema. "
                f"Expected: {expected_schema}, got: {dataframe.schema}"
            )

    return dataframe
