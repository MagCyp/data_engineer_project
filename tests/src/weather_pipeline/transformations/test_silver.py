from datetime import UTC, datetime

import polars as pl

from weather_pipeline.transformations.silver import (
    SILVER_COLUMNS,
    transform_bronze_to_silver,
)


def bronze_row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "location": "New York",
        "timezone": "GMT",
        "time": datetime(2025, 1, 1, 10, 0),
        "temperature_2m": 3.2,
        "relative_humidity_2m": 72,
        "precipitation": 0.0,
        "rain": 0.0,
        "wind_speed_10m": 8.1,
        "ingested_at": datetime(2026, 10, 7, 12, 0, tzinfo=UTC),
    }
    row.update(overrides)
    return row


def test_transform_bronze_to_silver_renames_and_keeps_latest_record() -> None:
    dataframe = pl.DataFrame(
        [
            bronze_row(
                temperature_2m=1.0,
                ingested_at=datetime(2026, 10, 7, 11, 0, tzinfo=UTC),
            ),
            bronze_row(temperature_2m=3.2),
            bronze_row(
                location=" Rome ",
                time=datetime(2025, 1, 1, 9, 0),
                temperature_2m=12.5,
            ),
        ]
    )

    result = transform_bronze_to_silver(dataframe)

    assert result.columns == SILVER_COLUMNS
    assert result.select("location").to_series().to_list() == [
        "New York",
        "Rome",
    ]
    assert result.filter(pl.col("location") == "New York").item(
        0,
        "temperature_c",
    ) == 3.2
    assert result["timezone"].to_list() == ["GMT", "GMT"]
