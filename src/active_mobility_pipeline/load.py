from pathlib import Path

from storage.database import (
    active_mobility_counts,
    active_mobility_sensors,
    load_parquet_to_table,
)

from .validation import (
    ACTIVE_MOBILITY_COUNT_SILVER_SCHEMA,
    ACTIVE_MOBILITY_SENSOR_SILVER_SCHEMA,
    validate_silver_active_mobility_counts,
    validate_silver_active_mobility_sensors,
)


def load_active_mobility_counts(file_path: str | Path) -> int:
    return load_parquet_to_table(
        file_path,
        schema=ACTIVE_MOBILITY_COUNT_SILVER_SCHEMA,
        validator=validate_silver_active_mobility_counts,
        table=active_mobility_counts,
    )


def load_active_mobility_sensors(file_path: str | Path) -> int:
    return load_parquet_to_table(
        file_path,
        schema=ACTIVE_MOBILITY_SENSOR_SILVER_SCHEMA,
        validator=validate_silver_active_mobility_sensors,
        table=active_mobility_sensors,
    )
