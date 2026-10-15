from collections.abc import Mapping, Sequence
from datetime import date
from typing import Any

from settings import get_api_config, get_pipeline_config
from weather_pipeline.ingestion.client import get_weather_data
from weather_pipeline.validation.models import (
    CityParams,
    HourlyWeatherResponse,
)


def get_location_by_name(
    city_name: str,
    locations: Sequence[CityParams | Mapping[str, Any]],
) -> CityParams:
    """Return the latitude and longitude for a given city name."""

    for location in locations:
        city_params = (
            location
            if isinstance(location, CityParams)
            else CityParams.model_validate(location)
        )
        if city_params.name == city_name:
            return city_params

    raise ValueError(f"City '{city_name}' not found in the configured locations.")


def fetch_weather_for_location(
    config: Mapping[str, Any],
    city_name: str | None = None,
    *,
    start_date: date,
    end_date: date,
) -> HourlyWeatherResponse:
    """Fetch historical hourly weather data for a given city name."""
    weather_config = get_pipeline_config(config, "weather")
    api_config = get_api_config(config, str(weather_config["api"]))
    selected_city = (
        str(weather_config["default_city"])
        if city_name is None
        else city_name
    )
    city_params = get_location_by_name(
        selected_city,
        weather_config["locations"],
    )
    return get_weather_data(
        city_params=city_params,
        base_url=str(api_config["base_url"]),
        timeout_seconds=int(api_config["timeout_seconds"]),
        start_date=start_date,
        end_date=end_date,
    )
