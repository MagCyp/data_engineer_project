from datetime import date, datetime
from pathlib import Path

import polars as pl
import pytest

from bike_pipeline.ingestion.service import read_bike_data

SOURCE_CSV = """countid,id,date,counts,status
1,101,06/03/2023 11:45:00 PM,3,0
2,101,06/04/2023 12:00:00 AM,4,0
3,101,06/04/2023 01:15:00 PM,5,0
4,101,06/05/2023 12:00:00 AM,6,0
"""


def test_read_bike_data_parses_and_filters_inclusive_date_range(
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "export.csv"
    file_path.write_text(SOURCE_CSV, encoding="utf-8")

    result = read_bike_data(
        file_path,
        start_date=date(2023, 6, 4),
        end_date=date(2023, 6, 4),
    )

    assert result["countid"].to_list() == [2, 3]
    assert result["date"].to_list() == [
        datetime(2023, 6, 4, 0, 0),
        datetime(2023, 6, 4, 13, 15),
    ]
    assert result.schema["date"] == pl.Datetime("us")


def test_read_bike_data_rejects_reversed_dates(tmp_path: Path) -> None:
    with pytest.raises(
        ValueError,
        match="start_date must be less than or equal to end_date",
    ):
        read_bike_data(
            tmp_path / "missing.csv",
            start_date=date(2023, 6, 5),
            end_date=date(2023, 6, 4),
        )


def test_read_bike_data_reports_invalid_source_values(tmp_path: Path) -> None:
    file_path = tmp_path / "export.csv"
    file_path.write_text(
        "countid,id,date,counts,status\n"
        "1,101,not-a-date,3,0\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Invalid bike source data"):
        read_bike_data(
            file_path,
            start_date=date(2023, 6, 4),
            end_date=date(2023, 6, 4),
        )
