from pathlib import Path

import polars as pl
import pytest

from storage.files.df_loader import load_df


def test_load_df_reads_parquet_and_validates_schema(tmp_path: Path) -> None:
    expected = pl.DataFrame({"city": ["New York"], "temperature": [12.5]})
    file_path = tmp_path / "weather.parquet"
    expected.write_parquet(file_path)

    result = load_df(file_path, expected.schema)

    assert result.equals(expected)


def test_load_df_rejects_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="does not exist"):
        load_df(tmp_path / "missing.parquet")


def test_load_df_wraps_parquet_read_error(tmp_path: Path) -> None:
    file_path = tmp_path / "broken.parquet"
    file_path.write_text("{}", encoding="utf-8")

    with pytest.raises(RuntimeError, match="Failed to load DataFrame"):
        load_df(file_path)


def test_load_df_rejects_unexpected_schema(tmp_path: Path) -> None:
    file_path = tmp_path / "weather.parquet"
    pl.DataFrame({"temperature": [12.5]}).write_parquet(file_path)

    with pytest.raises(ValueError, match="does not match"):
        load_df(file_path, pl.Schema({"temperature": pl.Int64}))
