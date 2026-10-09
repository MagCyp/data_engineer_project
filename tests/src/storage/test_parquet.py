from pathlib import Path

import polars as pl

from storage.parquet import save_as_parquet


def test_save_as_parquet_creates_parent_directories(tmp_path: Path) -> None:
    dataframe = pl.DataFrame({"value": [1, 2]})
    target_path = tmp_path / "nested" / "records.parquet"

    result = save_as_parquet(dataframe, target_path)

    assert result == target_path
    assert pl.read_parquet(target_path).equals(dataframe)
