import httpx

from weather_pipeline.validation.models import (
    CityParams,
    WeatherResponse,
    WeatherResponseHourly,
)


def get_weather_data(
    city_params: CityParams,
    base_url: str,
    timeout_seconds: int,
    hourly: list[str] | None = None,
) -> WeatherResponse | WeatherResponseHourly:
    """Fetch and validate current weather data from the Open-Meteo API."""
    params = {
        "latitude": city_params.latitude,
        "longitude": city_params.longitude,
        "current_weather": True,
        "hourly": hourly,
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

    return WeatherResponse.model_validate(response.json())
