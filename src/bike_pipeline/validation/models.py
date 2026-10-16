from datetime import datetime
from typing import Annotated, Any

import polars as pl
from pydantic import AfterValidator, BaseModel, ConfigDict, field_validator

from common.validation import (
    NaiveDateTime,
    NonEmptyString,
    NonNegativeInt,
    PositiveInt,
    UTCDateTime,
)

BIKE_SOURCE_DATETIME_FORMAT = "%m/%d/%Y %I:%M:%S %p"
BIKE_LOCAL_TIMEZONE = "America/New_York"
BIKE_AMBIGUOUS_TIME_POLICY = "earliest"
BIKE_ALLOWED_STATUSES = frozenset({0, 1, 2, 4, 8, 16})
BIKE_SOURCE_TIMEZONE_MAP = {
    "(UTC-05:00) US/Eastern;DST": BIKE_LOCAL_TIMEZONE,
}


def validate_bike_status(value: int) -> int:
    if value not in BIKE_ALLOWED_STATUSES:
        raise ValueError(f"unsupported bike status: {value}")
    return value


BikeStatus = Annotated[int, AfterValidator(validate_bike_status)]

BIKE_RAW_CSV_SCHEMA = pl.Schema(
    {
        "countid": pl.Int64,
        "id": pl.Int64,
        "date": pl.String,
        "counts": pl.String,
        "status": pl.Int64,
    }
)
BIKE_SOURCE_SCHEMA = pl.Schema(
    {
        **BIKE_RAW_CSV_SCHEMA,
        "counts": pl.Int64,
    }
)
BIKE_SOURCE_COLUMNS = tuple(BIKE_SOURCE_SCHEMA.names())

BIKE_COUNTER_SOURCE_SCHEMA = pl.Schema(
    {
        "id": pl.Int64,
        "name": pl.String,
        "domain": pl.String,
        "latitude": pl.String,
        "longitude": pl.String,
        "interval": pl.Int64,
        "timezone": pl.String,
        "sens": pl.Int64,
        "counter": pl.String,
    }
)
BIKE_COUNTER_SOURCE_COLUMNS = tuple(BIKE_COUNTER_SOURCE_SCHEMA.names())

BIKE_BRONZE_SCHEMA = pl.Schema(
    {
        **BIKE_SOURCE_SCHEMA,
        "date": pl.Datetime(time_unit="us"),
        "ingested_at": pl.Datetime(time_unit="us", time_zone="UTC"),
    }
)
BIKE_SILVER_SCHEMA = pl.Schema(
    {
        "record_id": pl.Int64,
        "counter_id": pl.Int64,
        "timezone": pl.String,
        "observed_at_local": pl.Datetime(time_unit="us"),
        "observed_at_utc": pl.Datetime(time_unit="us", time_zone="UTC"),
        "bike_count": pl.Int64,
        "status": pl.Int64,
        "ingested_at": pl.Datetime(time_unit="us", time_zone="UTC"),
    }
)

PositiveIdentifier = PositiveInt
NonNegativeCount = NonNegativeInt


class BikeSourceRecord(BaseModel):
    """One record as supplied by the bike CSV source."""

    model_config = ConfigDict(extra="forbid")

    countid: PositiveIdentifier
    id: PositiveIdentifier
    date: datetime
    counts: NonNegativeCount
    status: BikeStatus

    @field_validator("date", mode="before")
    @classmethod
    def parse_source_datetime(cls, value: Any) -> Any:
        if isinstance(value, str):
            return datetime.strptime(value, BIKE_SOURCE_DATETIME_FORMAT)
        return value

    @field_validator("counts", mode="before")
    @classmethod
    def parse_source_count(cls, value: Any) -> Any:
        if isinstance(value, str):
            return value.replace(",", "")
        return value

class BikeObservation(BaseModel):
    """Normalized bike observation ready for Silver storage."""

    model_config = ConfigDict(extra="forbid")

    record_id: PositiveIdentifier
    counter_id: PositiveIdentifier
    timezone: NonEmptyString
    observed_at_local: NaiveDateTime
    observed_at_utc: UTCDateTime
    bike_count: NonNegativeCount
    status: BikeStatus
    ingested_at: UTCDateTime
