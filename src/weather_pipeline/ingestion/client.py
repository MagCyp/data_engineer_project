from datetime import date

from common.http import RetryPolicy, get_with_retry
from helpers import validate_date_range
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
    max_retries: int,
    retry_base_delay_seconds: float,
    retry_max_delay_seconds: float,
) -> HourlyWeatherResponse:
    """Fetch and validate historical hourly weather data."""
    validate_date_range(start_date, end_date)

    params: dict[str, float | str] = {
        "latitude": city_params.latitude,
        "longitude": city_params.longitude,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "hourly": ",".join(HOURLY_PARAMETERS),
        "timezone": "GMT",
    }

    retry_policy = RetryPolicy(
        max_retries=max_retries,
        base_delay_seconds=retry_base_delay_seconds,
        max_delay_seconds=retry_max_delay_seconds,
    )

    response = get_with_retry(
        base_url,
        params=params,
        headers=None,
        timeout_seconds=timeout_seconds,
        retry_policy=retry_policy,
        request_name="weather data",
    )

    return HourlyWeatherResponse.model_validate(response.json())
