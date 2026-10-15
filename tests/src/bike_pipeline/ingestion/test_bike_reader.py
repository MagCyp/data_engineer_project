from pathlib import Path

import pytest

from bike_pipeline.ingestion.reader import scan_bike_counters_csv, scan_bike_csv
from bike_pipeline.validation.models import (
    BIKE_COUNTER_SOURCE_SCHEMA,
    BIKE_SOURCE_SCHEMA,
)

VALID_CSV = """countid,id,date,counts,status
19831896,100009425,06/03/2023 12:00:00 AM,"1,027",0
19831897,100009425,06/03/2023 12:15:00 AM,9,0
"""


def test_scan_bike_csv_returns_typed_lazy_frame(tmp_path: Path) -> None:
    file_path = tmp_path / "export.csv"
    file_path.write_text(VALID_CSV, encoding="utf-8")

    result = scan_bike_csv(file_path).collect()

    assert result.schema == BIKE_SOURCE_SCHEMA
    assert result.to_dicts() == [
        {
            "countid": 19831896,
            "id": 100009425,
            "date": "06/03/2023 12:00:00 AM",
            "counts": 1027,
            "status": 0,
        },
        {
            "countid": 19831897,
            "id": 100009425,
            "date": "06/03/2023 12:15:00 AM",
            "counts": 9,
            "status": 0,
        },
    ]


def test_scan_bike_csv_rejects_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="does not exist"):
        scan_bike_csv(tmp_path / "missing.csv")


def test_scan_bike_csv_rejects_unexpected_columns(tmp_path: Path) -> None:
    file_path = tmp_path / "export.csv"
    file_path.write_text("id,date,counts\n1,2025-01-01,2\n", encoding="utf-8")

    with pytest.raises(ValueError, match="columns do not match"):
        scan_bike_csv(file_path)


def test_scan_bike_csv_rejects_empty_file(tmp_path: Path) -> None:
    file_path = tmp_path / "export.csv"
    file_path.touch()

    with pytest.raises(ValueError, match="file is empty"):
        scan_bike_csv(file_path)


def test_scan_bike_counters_csv_returns_typed_metadata(
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "counters.csv"
    file_path.write_text(
        "id,name,domain,latitude,longitude,interval,timezone,sens,counter\n"
        '101,Main St,NYC DOT,"40,123","-73,123",15,'
        "(UTC-05:00) US/Eastern;DST,5,Y123\n",
        encoding="utf-8",
    )

    result = scan_bike_counters_csv(file_path).collect()

    assert result.schema == BIKE_COUNTER_SOURCE_SCHEMA
    assert result.item(0, "timezone") == "(UTC-05:00) US/Eastern;DST"
