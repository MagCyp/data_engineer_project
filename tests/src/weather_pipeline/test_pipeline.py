from datetime import date
from pathlib import Path
from unittest.mock import Mock

import polars as pl
import pytest

import weather_pipeline.pipeline as pipeline
from weather_pipeline.validation.models import HourlyWeatherResponse


def test_process_weather_month_writes_bronze_and_silver_parquet(
    hourly_weather_payload: dict[str, object],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    response = HourlyWeatherResponse.model_validate(hourly_weather_payload)
    fetch_weather = Mock(return_value=response)

    def get_output_path(
        config: object,
        *,
        location: str,
        year: int,
        month: int,
        storage_key: str,
    ) -> Path:
        del config
        return (
            tmp_path
            / storage_key
            / location
            / f"{year}-{month:02d}.parquet"
        )

    monkeypatch.setattr(pipeline, "fetch_weather_for_location", fetch_weather)
    monkeypatch.setattr(
        pipeline,
        "get_weather_observations_path",
        get_output_path,
    )

    start_date = date(2026, 10, 1)
    end_date = date(2026, 10, 31)
    config: dict[str, object] = {}

    pipeline.process_weather_month(
        config,
        "New York",
        start_date,
        end_date,
    )

    fetch_weather.assert_called_once_with(
        config,
        "New York",
        start_date=start_date,
        end_date=end_date,
    )

    bronze = pl.read_parquet(
        tmp_path / "bronze_path" / "New York" / "2026-10.parquet"
    )
    silver = pl.read_parquet(
        tmp_path / "silver_path" / "New York" / "2026-10.parquet"
    )

    assert bronze.height == 2
    assert bronze["location"].to_list() == ["New York", "New York"]
    assert "time" in bronze.columns
    assert bronze.schema["time"].time_zone == "UTC"
    assert silver.height == 2
    assert "observed_at_utc" in silver.columns
    assert silver.schema["observed_at_utc"].time_zone == "UTC"
    assert "temperature_c" in silver.columns
    assert "time" not in silver.columns

    updated_response = response.model_copy(deep=True)
    updated_response.hourly.temperature_2m[0] = 25.0
    fetch_weather.return_value = updated_response

    pipeline.process_weather_month(
        config,
        "New York",
        start_date,
        end_date,
    )

    rerun_silver = pl.read_parquet(
        tmp_path / "silver_path" / "New York" / "2026-10.parquet"
    ).sort("observed_at_utc")
    assert rerun_silver.height == 2
    assert rerun_silver["temperature_c"].to_list() == [25.0, 19.7]


def test_process_weather_month_rejects_dates_from_different_months() -> None:
    with pytest.raises(
        ValueError,
        match="start_date and end_date must belong to the same month",
    ):
        pipeline.process_weather_month(
            {},
            "New York",
            date(2026, 10, 1),
            date(2026, 11, 1),
        )
