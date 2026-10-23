from pathlib import Path
from unittest.mock import Mock, call

import pytest

import active_mobility_pipeline.load as load
from active_mobility_pipeline.validation import (
    ACTIVE_MOBILITY_COUNT_SILVER_SCHEMA,
    ACTIVE_MOBILITY_SENSOR_SILVER_SCHEMA,
    validate_silver_active_mobility_counts,
    validate_silver_active_mobility_sensors,
)
from storage.database import active_mobility_counts, active_mobility_sensors


def test_load_functions_use_the_matching_schema_validator_and_table(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    counts_path = tmp_path / "counts.parquet"
    sensors_path = tmp_path / "sensors.parquet"
    loader = Mock(side_effect=[12, 3])
    monkeypatch.setattr(load, "load_parquet_to_table", loader)

    assert load.load_active_mobility_counts(counts_path) == 12
    assert load.load_active_mobility_sensors(sensors_path) == 3
    assert loader.call_args_list == [
        call(
            counts_path,
            schema=ACTIVE_MOBILITY_COUNT_SILVER_SCHEMA,
            validator=validate_silver_active_mobility_counts,
            table=active_mobility_counts,
        ),
        call(
            sensors_path,
            schema=ACTIVE_MOBILITY_SENSOR_SILVER_SCHEMA,
            validator=validate_silver_active_mobility_sensors,
            table=active_mobility_sensors,
        ),
    ]

