from pathlib import Path

from storage.database import bike_counts, load_parquet_to_table

from .validation import BIKE_SILVER_SCHEMA, validate_silver_bike


def load_bike(file_path: str | Path) -> int:
    """Validate a Silver bike Parquet file and upsert it into PostgreSQL."""
    return load_parquet_to_table(
        file_path,
        schema=BIKE_SILVER_SCHEMA,
        validator=validate_silver_bike,
        table=bike_counts,
    )
