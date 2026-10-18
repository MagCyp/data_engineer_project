from collections.abc import Mapping
from datetime import date
from typing import Any

from helpers import validate_month_range
from storage import (
    get_weather_observations_path,
    save_as_parquet,
    weather_observations_to_dataframe,
)

from .ingestion import fetch_weather_for_location
from .transformations import (
    transform_bronze_to_silver,
    transform_response_to_bronze,
)
from .validation import validate_bronze_weather, validate_silver_weather


def process_weather_month(
    config: Mapping[str, Any],
    location: str,
    start_date: date,
    end_date: date,
) -> None:
    """Process weather data for a specific month."""
    validate_month_range(start_date, end_date)

    weather_raw_data = fetch_weather_for_location(
        config,
        location,
        start_date=start_date,
        end_date=end_date,
    )

    weather_bronze_data = transform_response_to_bronze(
        weather_raw_data,
        location,
    )

    bronze_dataframe = weather_observations_to_dataframe(weather_bronze_data)
    validated_bronze = validate_bronze_weather(bronze_dataframe)

    bronze_path = get_weather_observations_path(
        config,
        location=location,
        year=start_date.year,
        month=start_date.month,
        storage_key="bronze_path",
    )
    save_as_parquet(validated_bronze, bronze_path)

    silver_dataframe = transform_bronze_to_silver(validated_bronze)
    validated_silver = validate_silver_weather(silver_dataframe)

    silver_path = get_weather_observations_path(
        config,
        location=location,
        year=start_date.year,
        month=start_date.month,
        storage_key="silver_path",
    )
    save_as_parquet(validated_silver, silver_path)
