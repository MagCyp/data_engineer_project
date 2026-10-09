from datetime import datetime
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

Percentage = Annotated[int, Field(ge=0, le=100)]
NonNegativeFloat = Annotated[float, Field(ge=0)]


class WeatherResponse(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    generationtime_ms: float = Field(ge=0)
    utc_offset_seconds: int
    timezone: str
    timezone_abbreviation: str
    elevation: float


class HourlyWeatherUnits(BaseModel):
    time: str
    temperature_2m: str
    rain: str
    wind_speed_10m: str
    precipitation: str
    relative_humidity_2m: str


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
    model_config = ConfigDict(str_strip_whitespace=True)

    location: str = Field(min_length=1)
    timezone: str = Field(min_length=1)
    time: datetime
    temperature_2m: float
    rain: NonNegativeFloat
    wind_speed_10m: NonNegativeFloat
    precipitation: NonNegativeFloat
    relative_humidity_2m: Percentage
    ingested_at: datetime


class CityParams(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
