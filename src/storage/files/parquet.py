from pathlib import Path

import polars as pl


def save_as_parquet(
    dataframe: pl.DataFrame,
    path: str | Path,
) -> Path:
    """Write a Polars DataFrame to a Parquet file."""
    target_path = Path(path)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    dataframe.write_parquet(target_path)
    return target_path
