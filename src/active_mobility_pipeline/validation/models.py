from typing import Literal, Self

import polars as pl
from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from common.validation import (
    Latitude,
    Longitude,
    NaiveDateTime,
    NonEmptyString,
    NonNegativeInt,
    UTCDateTime,
)

ACTIVE_MOBILITY_LOCAL_TIMEZONE = "America/New_York"
ACTIVE_MOBILITY_AMBIGUOUS_TIME_POLICY = "earliest"
ACTIVE_MOBILITY_INTERVALS = {"PT15M": 15, "PT1H": 60}
ACTIVE_MOBILITY_TRAVEL_MODES = frozenset({"bike", "pedestrian", "scooter"})
ACTIVE_MOBILITY_DIRECTIONS = frozenset({"in", "out"})
ACTIVE_MOBILITY_STATUSES = frozenset({"raw", "modified", "deleted"})

ACTIVE_MOBILITY_COUNT_SOURCE_SCHEMA = pl.Schema(
    {
        "sensor_id": pl.String,
        "travelmode": pl.String,
        "direction": pl.String,
        "flowid": pl.String,
        "flowname": pl.String,
        "timestamp": pl.Datetime(time_unit="us"),
        "granularity": pl.String,
        "counts": pl.Int64,
        "status": pl.String,
    }
)
ACTIVE_MOBILITY_COUNT_SOURCE_FIELDS = tuple(
    ACTIVE_MOBILITY_COUNT_SOURCE_SCHEMA.names()
)
ACTIVE_MOBILITY_COUNT_BRONZE_SCHEMA = pl.Schema(
    {
        **ACTIVE_MOBILITY_COUNT_SOURCE_SCHEMA,
        "ingested_at": pl.Datetime(time_unit="us", time_zone="UTC"),
    }
)
ACTIVE_MOBILITY_COUNT_SILVER_SCHEMA = pl.Schema(
    {
        "sensor_id": pl.String,
        "flow_id": pl.String,
        "flow_name": pl.String,
        "travel_mode": pl.String,
        "direction": pl.String,
        "timezone": pl.String,
        "observed_at_local": pl.Datetime(time_unit="us"),
        "observed_at_utc": pl.Datetime(time_unit="us", time_zone="UTC"),
        "interval_minutes": pl.Int64,
        "mobility_count": pl.Int64,
        "source_status": pl.String,
        "ingested_at": pl.Datetime(time_unit="us", time_zone="UTC"),
    }
)

ACTIVE_MOBILITY_SENSOR_SOURCE_SCHEMA = pl.Schema(
    {
        "id": pl.String,
        "name": pl.String,
        "lat": pl.Float64,
        "lon": pl.Float64,
        "firstdata": pl.Datetime(time_unit="us"),
        "lastdata": pl.Datetime(time_unit="us"),
        "granularity": pl.String,
        "travelmodes": pl.String,
        "directional": pl.Boolean,
        "hastimestampeddata": pl.Boolean,
        "hasweather": pl.Boolean,
        "counters_id": pl.String,
        "counters_serial": pl.String,
        "counters_installationdate": pl.Datetime(time_unit="us"),
        "counters_detachmentdate": pl.Datetime(time_unit="us"),
        "domain_name": pl.String,
    }
)
ACTIVE_MOBILITY_SENSOR_SOURCE_FIELDS = tuple(
    ACTIVE_MOBILITY_SENSOR_SOURCE_SCHEMA.names()
)
ACTIVE_MOBILITY_SENSOR_BRONZE_SCHEMA = pl.Schema(
    {
        **ACTIVE_MOBILITY_SENSOR_SOURCE_SCHEMA,
        "ingested_at": pl.Datetime(time_unit="us", time_zone="UTC"),
    }
)
ACTIVE_MOBILITY_SENSOR_SILVER_SCHEMA = pl.Schema(
    {
        "sensor_id": pl.String,
        "sensor_name": pl.String,
        "latitude": pl.Float64,
        "longitude": pl.Float64,
        "timezone": pl.String,
        "first_observed_at_local": pl.Datetime(time_unit="us"),
        "last_observed_at_local": pl.Datetime(time_unit="us"),
        "recording_interval_minutes": pl.Int64,
        "travel_modes": pl.String,
        "is_directional": pl.Boolean,
        "has_timestamped_data": pl.Boolean,
        "has_weather": pl.Boolean,
        "operator_name": pl.String,
        "ingested_at": pl.Datetime(time_unit="us", time_zone="UTC"),
    }
)


def _interval_minutes(value: str) -> int:
    try:
        return ACTIVE_MOBILITY_INTERVALS[value]
    except KeyError as error:
        raise ValueError(f"unsupported granularity: {value}") from error


class ActiveMobilityCountSourceRecord(BaseModel):
    """One count record returned by the NYC Open Data API."""

    model_config = ConfigDict(extra="forbid")

    sensor_id: NonEmptyString
    travelmode: Literal["bike", "pedestrian", "scooter"]
    direction: Literal["in", "out"]
    flowid: NonEmptyString
    flowname: NonEmptyString | None = None
    timestamp: NaiveDateTime
    granularity: Literal["PT15M", "PT1H"]
    counts: NonNegativeInt | None = None
    status: Literal["raw", "modified", "deleted"]

    @model_validator(mode="after")
    def ensure_timestamp_matches_granularity(self) -> Self:
        interval_minutes = _interval_minutes(self.granularity)
        if (
            self.timestamp.minute % interval_minutes != 0
            or self.timestamp.second != 0
            or self.timestamp.microsecond != 0
        ):
            raise ValueError("timestamp must align with granularity")
        return self


class ActiveMobilitySensorSourceRecord(BaseModel):
    """One sensor-metadata record returned by the NYC Open Data API."""

    model_config = ConfigDict(extra="forbid")

    id: NonEmptyString
    name: NonEmptyString
    lat: Latitude | None = None
    lon: Longitude | None = None
    firstdata: NaiveDateTime
    lastdata: NaiveDateTime
    granularity: Literal["PT15M", "PT1H"]
    travelmodes: NonEmptyString
    directional: bool
    hastimestampeddata: bool
    hasweather: bool
    counters_id: NonEmptyString | None = None
    counters_serial: NonEmptyString | None = None
    counters_installationdate: NaiveDateTime | None = None
    counters_detachmentdate: NaiveDateTime | None = None
    domain_name: NonEmptyString

    @field_validator("travelmodes")
    @classmethod
    def normalize_travel_modes(cls, value: str) -> str:
        modes = tuple(mode.strip().casefold() for mode in value.split(","))
        unsupported = set(modes).difference(ACTIVE_MOBILITY_TRAVEL_MODES)
        if unsupported:
            raise ValueError(f"unsupported travel modes: {sorted(unsupported)}")
        return ", ".join(modes)

    @model_validator(mode="after")
    def ensure_coordinate_pair(self) -> Self:
        if (self.lat is None) != (self.lon is None):
            raise ValueError("lat and lon must either both be set or both be null")
        return self


class ActiveMobilityCountObservation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sensor_id: NonEmptyString
    flow_id: NonEmptyString
    flow_name: NonEmptyString | None = None
    travel_mode: Literal["bike", "pedestrian", "scooter"]
    direction: Literal["in", "out"]
    timezone: NonEmptyString
    observed_at_local: NaiveDateTime
    observed_at_utc: UTCDateTime
    interval_minutes: Literal[15, 60]
    mobility_count: NonNegativeInt | None = None
    source_status: Literal["raw", "modified", "deleted"]
    ingested_at: UTCDateTime


class ActiveMobilitySensor(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sensor_id: NonEmptyString
    sensor_name: NonEmptyString
    latitude: Latitude
    longitude: Longitude
    timezone: NonEmptyString
    first_observed_at_local: NaiveDateTime
    last_observed_at_local: NaiveDateTime
    recording_interval_minutes: Literal[15, 60]
    travel_modes: NonEmptyString
    is_directional: bool
    has_timestamped_data: bool
    has_weather: bool
    operator_name: NonEmptyString
    ingested_at: UTCDateTime
