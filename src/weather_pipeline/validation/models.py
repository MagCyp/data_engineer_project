from datetime import datetime
from typing import Self

import polars as pl
from pydantic import BaseModel, model_validator

from common.validation import (
    Latitude,
    Longitude,
    NonEmptyString,
    NonNegativeFloat,
    Percentage,
    UTCDateTime,
)

WEATHER_BRONZE_SCHEMA = pl.Schema(
    {
        "location": pl.String,
        "timezone": pl.String,
        "time": pl.Datetime(time_unit="us", time_zone="UTC"),
        "temperature_2m": pl.Float64,
        "rain": pl.Float64,
        "wind_speed_10m": pl.Float64,
        "precipitation": pl.Float64,
        "relative_humidity_2m": pl.Int64,
        "ingested_at": pl.Datetime(time_unit="us", time_zone="UTC"),
    }
)
WEATHER_SILVER_SCHEMA = pl.Schema(
    {
        "location": pl.String,
        "timezone": pl.String,
        "observed_at_utc": pl.Datetime(time_unit="us", time_zone="UTC"),
        "temperature_c": pl.Float64,
        "relative_humidity_pct": pl.Int64,
        "precipitation_mm": pl.Float64,
        "rain_mm": pl.Float64,
        "wind_speed_kmh": pl.Float64,
        "ingested_at": pl.Datetime(time_unit="us", time_zone="UTC"),
    }
)


class WeatherResponse(BaseModel):
    latitude: Latitude
    longitude: Longitude
    generationtime_ms: NonNegativeFloat
    utc_offset_seconds: int
    timezone: NonEmptyString
    timezone_abbreviation: NonEmptyString
    elevation: float


class HourlyWeatherUnits(BaseModel):
    time: NonEmptyString
    temperature_2m: NonEmptyString
    rain: NonEmptyString
    wind_speed_10m: NonEmptyString
    precipitation: NonEmptyString
    relative_humidity_2m: NonEmptyString


class HourlyWeather(BaseModel):
    time: list[datetime]
    temperature_2m: list[float]
    rain: list[NonNegativeFloat]
    wind_speed_10m: list[NonNegativeFloat]
    precipitation: list[NonNegativeFloat]
    relative_humidity_2m: list[Percentage]

    @model_validator(mode="after")
    def ensure_equal_series_lengths(self) -> Self:
        expected_length = len(self.time)
        series = (
            self.temperature_2m,
            self.rain,
            self.wind_speed_10m,
            self.precipitation,
            self.relative_humidity_2m,
        )

        if any(len(values) != expected_length for values in series):
            raise ValueError("All hourly weather series must have equal lengths")

        return self


class HourlyWeatherResponse(WeatherResponse):
    hourly_units: HourlyWeatherUnits
    hourly: HourlyWeather


class WeatherObservation(BaseModel):
    location: NonEmptyString
    timezone: NonEmptyString
    time: UTCDateTime
    temperature_2m: float
    rain: NonNegativeFloat
    wind_speed_10m: NonNegativeFloat
    precipitation: NonNegativeFloat
    relative_humidity_2m: Percentage
    ingested_at: UTCDateTime


class CityParams(BaseModel):
    name: NonEmptyString
    latitude: Latitude
    longitude: Longitude
