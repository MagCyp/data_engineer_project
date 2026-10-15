from datetime import UTC, datetime
from typing import Annotated, Any

import polars as pl
from pydantic import BaseModel, ConfigDict, Field, field_validator

BIKE_SOURCE_DATETIME_FORMAT = "%m/%d/%Y %I:%M:%S %p"
BIKE_LOCAL_TIMEZONE = "America/New_York"
BIKE_AMBIGUOUS_TIME_POLICY = "earliest"
BIKE_ALLOWED_STATUSES = frozenset({0, 1, 2, 4, 8, 16})
BIKE_SOURCE_TIMEZONE_MAP = {
    "(UTC-05:00) US/Eastern;DST": BIKE_LOCAL_TIMEZONE,
}

# ``counts`` is read as text first because the source uses values such as
# ``"1,098"``. ``scan_bike_csv`` removes the thousands separator and exposes
# the typed BIKE_SOURCE_SCHEMA to the rest of the pipeline.
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

PositiveIdentifier = Annotated[int, Field(gt=0)]
NonNegativeCount = Annotated[int, Field(ge=0)]


class BikeSourceRecord(BaseModel):
    """One record as supplied by the bike CSV source."""

    model_config = ConfigDict(extra="forbid")

    countid: PositiveIdentifier
    id: PositiveIdentifier
    date: datetime
    counts: NonNegativeCount
    status: int

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

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: int) -> int:
        if value not in BIKE_ALLOWED_STATUSES:
            raise ValueError(f"unsupported bike status: {value}")
        return value


class BikeObservation(BaseModel):
    """Normalized bike observation ready for Silver storage."""

    model_config = ConfigDict(extra="forbid")

    record_id: PositiveIdentifier
    counter_id: PositiveIdentifier
    timezone: str = Field(min_length=1)
    observed_at_local: datetime
    observed_at_utc: datetime
    bike_count: NonNegativeCount
    status: int
    ingested_at: datetime

    @field_validator("observed_at_local")
    @classmethod
    def ensure_local_datetime_is_naive(cls, value: datetime) -> datetime:
        if value.tzinfo is not None and value.utcoffset() is not None:
            raise ValueError("observed_at_local must not contain a timezone")
        return value

    @field_validator("observed_at_utc", "ingested_at")
    @classmethod
    def ensure_datetime_is_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("UTC timestamps must be timezone-aware")
        return value.astimezone(UTC)

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: int) -> int:
        if value not in BIKE_ALLOWED_STATUSES:
            raise ValueError(f"unsupported bike status: {value}")
        return value
