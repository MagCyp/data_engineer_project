from pathlib import Path

from storage.database import load_parquet_to_table, subway_ridership

from .validation import SUBWAY_SILVER_SCHEMA, validate_silver_subway


def load_subway(file_path: str | Path) -> int:
    """Validate a Silver subway Parquet file and upsert it into PostgreSQL."""
    return load_parquet_to_table(
        file_path,
        schema=SUBWAY_SILVER_SCHEMA,
        validator=validate_silver_subway,
        table=subway_ridership,
    )
