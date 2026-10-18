from pathlib import Path

from storage.database import get_engine, subway_ridership, upsert_dataframe
from storage.files import load_df

from .validation import SUBWAY_SILVER_SCHEMA, validate_silver_subway

SILVER_SUBWAY_SCHEMA = SUBWAY_SILVER_SCHEMA


def load_subway(file_path: str | Path) -> int:
    """Validate a Silver subway Parquet file and upsert it into PostgreSQL."""
    dataframe = load_df(file_path, schema=SILVER_SUBWAY_SCHEMA)
    validated_subway = validate_silver_subway(dataframe)

    engine = get_engine()
    try:
        with engine.begin() as connection:
            return upsert_dataframe(
                validated_subway,
                connection,
                subway_ridership,
            )
    finally:
        engine.dispose()
