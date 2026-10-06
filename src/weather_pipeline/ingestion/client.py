from datetime import date

import httpx

from weather_pipeline.validation.models import (
    CityParams,
    HourlyWeatherResponse,
)

HOURLY_PARAMETERS = (
    "temperature_2m",
    "rain",
    "wind_speed_10m",
    "precipitation",
    "relative_humidity_2m",
)


def get_weather_data(
    city_params: CityParams,
    base_url: str,
    timeout_seconds: int,
    *,
    start_date: date,
    end_date: date,
) -> HourlyWeatherResponse:
    """Fetch and validate historical hourly weather data."""
    if start_date > end_date:
        raise ValueError("start_date must be before or equal to end_date")

    params: dict[str, float | str] = {
        "latitude": city_params.latitude,
        "longitude": city_params.longitude,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "hourly": ",".join(HOURLY_PARAMETERS),
    }

    try:
        response = httpx.get(base_url, params=params, timeout=timeout_seconds)
        response.raise_for_status()
    except httpx.RequestError as error:
        raise RuntimeError(
            f"An error occurred while requesting weather data: {error}"
        ) from error
    except httpx.HTTPStatusError as error:
        raise RuntimeError(
            f"HTTP error occurred: {error.response.status_code} - {error.response.text}"
        ) from error

    return HourlyWeatherResponse.model_validate(response.json())
