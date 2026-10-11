from datetime import UTC, datetime

import polars as pl
import pytest

from weather_pipeline.validation.bronze import validate_bronze_weather


def bronze_row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "location": "New York",
        "timezone": "GMT",
        "time": datetime(2025, 1, 1, 10, 0, tzinfo=UTC),
        "temperature_2m": 3.2,
        "relative_humidity_2m": 72,
        "precipitation": 0.0,
        "rain": 0.0,
        "wind_speed_10m": 8.1,
        "ingested_at": datetime(2026, 10, 7, 12, 0, tzinfo=UTC),
    }
    row.update(overrides)
    return row


def test_validate_bronze_weather_returns_valid_data_unchanged() -> None:
    dataframe = pl.DataFrame([bronze_row()])

    result = validate_bronze_weather(dataframe)

    assert result is dataframe


@pytest.mark.parametrize(
    ("field", "invalid_value"),
    [
        ("location", None),
        ("location", "   "),
        ("timezone", None),
        ("time", None),
        ("temperature_2m", None),
        ("temperature_2m", float("nan")),
        ("relative_humidity_2m", -1),
        ("relative_humidity_2m", 101),
        ("precipitation", -0.1),
        ("rain", -0.1),
        ("wind_speed_10m", -0.1),
        ("ingested_at", None),
    ],
)
def test_validate_bronze_weather_rejects_invalid_rows(
    field: str,
    invalid_value: object,
) -> None:
    invalid_overrides: dict[str, object] = {"location": "Invalid"}
    invalid_overrides[field] = invalid_value
    dataframe = pl.DataFrame(
        [
            bronze_row(),
            bronze_row(**invalid_overrides),
        ]
    )

    with pytest.raises(
        ValueError,
        match="Bronze weather validation failed for 1 row",
    ):
        validate_bronze_weather(dataframe)


def test_validate_bronze_weather_rejects_missing_columns() -> None:
    dataframe = pl.DataFrame([bronze_row()]).drop("rain")

    with pytest.raises(ValueError, match="Missing bronze columns: rain"):
        validate_bronze_weather(dataframe)


def test_validate_bronze_weather_rejects_naive_observation_time() -> None:
    dataframe = pl.DataFrame([bronze_row()]).with_columns(
        pl.col("time").dt.replace_time_zone(None)
    )

    with pytest.raises(
        ValueError,
        match="Bronze column 'time' must use UTC timezone",
    ):
        validate_bronze_weather(dataframe)
