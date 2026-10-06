from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class CurrentWeatherUnits(BaseModel):
    time: str
    interval: str
    temperature: str
    windspeed: str
    winddirection: str
    is_day: str
    weathercode: str


class CurrentWeather(BaseModel):
    time: datetime
    interval: int
    temperature: float
    windspeed: float
    winddirection: float
    is_day: Literal[0, 1]
    weathercode: int


class WeatherResponse(BaseModel):
    latitude: float
    longitude: float
    generationtime_ms: float
    utc_offset_seconds: int
    timezone: str
    timezone_abbreviation: str
    elevation: float
    current_weather_units: CurrentWeatherUnits
    current_weather: CurrentWeather


class WeatherResponseHourly(WeatherResponse):
    hourly: dict[str, list[float | str | int]]


class CityParams(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
