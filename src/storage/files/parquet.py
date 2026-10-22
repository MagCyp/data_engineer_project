from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Sequence

import polars as pl


def _atomic_write_parquet(dataframe: pl.DataFrame, target_path: Path) -> None:
    """Write a Parquet file without exposing a partially written target."""
    temporary_path: Path | None = None
    try:
        with NamedTemporaryFile(
            dir=target_path.parent,
            prefix=f".{target_path.stem}-",
            suffix=target_path.suffix,
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)

        dataframe.write_parquet(temporary_path)
        temporary_path.replace(target_path)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def save_as_parquet(
    dataframe: pl.DataFrame,
    path: str | Path,
) -> Path:
    """Atomically write a Polars DataFrame to a Parquet file."""
    target_path = Path(path)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    _atomic_write_parquet(dataframe, target_path)
    return target_path


def merge_and_save_parquet(
    dataframe: pl.DataFrame,
    path: str | Path,
    *,
    key_columns: Sequence[str],
) -> Path:
    """Merge new rows into a Parquet file, with new keys taking precedence."""
    target_path = Path(path)
    normalized_keys = tuple(key_columns)
    if not normalized_keys:
        raise ValueError("key_columns must not be empty")
    if len(set(normalized_keys)) != len(normalized_keys):
        raise ValueError("key_columns must not contain duplicates")

    missing_columns = set(normalized_keys).difference(dataframe.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"DataFrame is missing key columns: {missing}")
    if dataframe.select(normalized_keys).is_duplicated().any():
        raise ValueError("New Parquet data contains duplicate key values")

    if not target_path.is_file():
        return save_as_parquet(dataframe, target_path)
    if dataframe.is_empty():
        return target_path

    existing = pl.read_parquet(target_path)
    missing_existing_columns = set(normalized_keys).difference(existing.columns)
    if missing_existing_columns:
        missing = ", ".join(sorted(missing_existing_columns))
        raise ValueError(f"Existing Parquet file is missing key columns: {missing}")
    if existing.select(normalized_keys).is_duplicated().any():
        raise ValueError("Existing Parquet file contains duplicate key values")

    merged = pl.concat((existing, dataframe), how="vertical").unique(
        subset=normalized_keys,
        keep="last",
        maintain_order=True,
    )
    save_as_parquet(merged, target_path)
    return target_path
