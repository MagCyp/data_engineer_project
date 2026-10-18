from datetime import UTC, datetime

import polars as pl
import pytest

from weather_pipeline.validation.silver import validate_silver_weather


def silver_row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "location": "New York",
        "timezone": "GMT",
        "observed_at_utc": datetime(2025, 1, 1, 10, 0, tzinfo=UTC),
        "temperature_c": 3.2,
        "relative_humidity_pct": 72,
        "precipitation_mm": 0.0,
        "rain_mm": 0.0,
        "wind_speed_kmh": 8.1,
        "ingested_at": datetime(2026, 10, 7, 12, 0, tzinfo=UTC),
    }
    row.update(overrides)
    return row


def test_validate_silver_weather_returns_valid_data_unchanged() -> None:
    dataframe = pl.DataFrame([silver_row()])

    result = validate_silver_weather(dataframe)

    assert result is dataframe


@pytest.mark.parametrize(
    ("field", "invalid_value"),
    [
        ("location", None),
        ("location", "   "),
        ("timezone", None),
        ("observed_at_utc", None),
        ("temperature_c", None),
        ("temperature_c", float("nan")),
        ("relative_humidity_pct", -1),
        ("relative_humidity_pct", 101),
        ("precipitation_mm", -0.1),
        ("rain_mm", -0.1),
        ("wind_speed_kmh", -0.1),
        ("ingested_at", None),
    ],
)
def test_validate_silver_weather_rejects_invalid_rows(
    field: str,
    invalid_value: object,
) -> None:
    invalid_overrides: dict[str, object] = {"location": "Invalid"}
    invalid_overrides[field] = invalid_value
    dataframe = pl.DataFrame(
        [
            silver_row(),
            silver_row(**invalid_overrides),
        ]
    )

    with pytest.raises(
        ValueError,
        match="Silver weather validation failed for 1 row",
    ):
        validate_silver_weather(dataframe)


def test_validate_silver_weather_rejects_missing_columns() -> None:
    dataframe = pl.DataFrame([silver_row()]).drop("rain_mm")

    with pytest.raises(
        ValueError,
        match="Missing Silver weather columns: rain_mm",
    ):
        validate_silver_weather(dataframe)


def test_validate_silver_weather_rejects_naive_observation_time() -> None:
    dataframe = pl.DataFrame([silver_row()]).with_columns(
        pl.col("observed_at_utc").dt.replace_time_zone(None)
    )

    with pytest.raises(
        ValueError,
        match="Silver weather column 'observed_at_utc' must use",
    ):
        validate_silver_weather(dataframe)
