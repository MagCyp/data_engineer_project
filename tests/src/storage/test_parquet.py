from pathlib import Path

import polars as pl
import pytest

from storage.files.parquet import merge_and_save_parquet, save_as_parquet


def test_save_as_parquet_creates_parent_directories(tmp_path: Path) -> None:
    dataframe = pl.DataFrame({"value": [1, 2]})
    target_path = tmp_path / "nested" / "records.parquet"

    result = save_as_parquet(dataframe, target_path)

    assert result == target_path
    assert pl.read_parquet(target_path).equals(dataframe)


def test_merge_and_save_parquet_retains_and_replaces_rows(tmp_path: Path) -> None:
    target_path = tmp_path / "records.parquet"
    first = pl.DataFrame(
        {"id": [1, 2], "value": ["first", "old"]}
    )
    second = pl.DataFrame(
        {"id": [2, 3], "value": ["new", "third"]}
    )

    merge_and_save_parquet(first, target_path, key_columns=("id",))
    merge_and_save_parquet(second, target_path, key_columns=("id",))

    result = pl.read_parquet(target_path).sort("id")
    expected = pl.DataFrame(
        {"id": [1, 2, 3], "value": ["first", "new", "third"]}
    )
    assert result.equals(expected)

    merge_and_save_parquet(
        second.head(0),
        target_path,
        key_columns=("id",),
    )
    assert pl.read_parquet(target_path).sort("id").equals(expected)


def test_merge_and_save_parquet_rejects_duplicate_new_keys(
    tmp_path: Path,
) -> None:
    target_path = tmp_path / "records.parquet"
    dataframe = pl.DataFrame({"id": [1, 1], "value": ["a", "b"]})

    with pytest.raises(ValueError, match="duplicate key values"):
        merge_and_save_parquet(dataframe, target_path, key_columns=("id",))

    assert not target_path.exists()


def test_failed_parquet_write_preserves_existing_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target_path = tmp_path / "records.parquet"
    existing = pl.DataFrame({"id": [1], "value": ["existing"]})
    update = pl.DataFrame({"id": [2], "value": ["new"]})
    save_as_parquet(existing, target_path)

    def fail_write(*args: object, **kwargs: object) -> None:
        del args, kwargs
        raise OSError("simulated write failure")

    monkeypatch.setattr(pl.DataFrame, "write_parquet", fail_write)

    with pytest.raises(OSError, match="simulated write failure"):
        merge_and_save_parquet(update, target_path, key_columns=("id",))

    assert pl.read_parquet(target_path).equals(existing)
    assert list(tmp_path.glob(".records-*.parquet")) == []
