from pathlib import Path

from storage.database import bike_counts, get_engine, upsert_dataframe
from storage.files import load_df

from .validation import BIKE_SILVER_SCHEMA, validate_silver_bike

SILVER_BIKE_SCHEMA = BIKE_SILVER_SCHEMA


def load_bike(file_path: str | Path) -> int:
    """Validate a Silver bike Parquet file and upsert it into PostgreSQL."""
    dataframe = load_df(file_path, schema=SILVER_BIKE_SCHEMA)
    validated_bike = validate_silver_bike(dataframe)

    engine = get_engine()
    try:
        with engine.begin() as connection:
            return upsert_dataframe(
                validated_bike,
                connection,
                bike_counts,
            )
    finally:
        engine.dispose()
