from storage.database import LANDING_SCHEMA, metadata
from storage.database.tables import (
    active_mobility_counts,
    active_mobility_sensors,
)


def test_active_mobility_tables_are_registered() -> None:
    assert active_mobility_counts.schema == LANDING_SCHEMA
    assert active_mobility_sensors.schema == LANDING_SCHEMA
    assert (
        metadata.tables["landing.active_mobility_counts"]
        is active_mobility_counts
    )
    assert (
        metadata.tables["landing.active_mobility_sensors"]
        is active_mobility_sensors
    )


def test_active_mobility_counts_uses_source_grain_primary_key() -> None:
    assert [
        column.name for column in active_mobility_counts.primary_key.columns
    ] == ["flow_id", "observed_at_utc", "interval_minutes"]


def test_active_mobility_sensors_uses_sensor_id_primary_key() -> None:
    assert [
        column.name for column in active_mobility_sensors.primary_key.columns
    ] == ["sensor_id"]


def test_active_mobility_sensor_coordinates_are_required() -> None:
    assert not active_mobility_sensors.c.latitude.nullable
    assert not active_mobility_sensors.c.longitude.nullable
