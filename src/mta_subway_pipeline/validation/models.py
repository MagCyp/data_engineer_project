from datetime import datetime
from typing import Literal, Self

import polars as pl
from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from common.validation import (
    Latitude,
    Longitude,
    NaiveDateTime,
    NonEmptyString,
    NonNegativeFloat,
    UTCDateTime,
)

SUBWAY_LOCAL_TIMEZONE = "America/New_York"
SUBWAY_AMBIGUOUS_TIME_POLICY = "earliest"
SUBWAY_SOURCE_SCHEMA = pl.Schema(
    {
        "transit_timestamp": pl.Datetime(time_unit="us"),
        "transit_mode": pl.String,
        "station_complex_id": pl.String,
        "station_complex": pl.String,
        "borough": pl.String,
        "payment_method": pl.String,
        "fare_class_category": pl.String,
        "ridership": pl.Float64,
        "transfers": pl.Float64,
        "latitude": pl.Float64,
        "longitude": pl.Float64,
        "georeference": pl.Struct(
            {
                "type": pl.String,
                "coordinates": pl.List(pl.Float64),
            }
        ),
    }
)
SUBWAY_SOURCE_FIELDS = tuple(SUBWAY_SOURCE_SCHEMA.names())
SUBWAY_BRONZE_SCHEMA = pl.Schema(
    {
        **SUBWAY_SOURCE_SCHEMA,
        "ingested_at": pl.Datetime(time_unit="us", time_zone="UTC"),
    }
)
SUBWAY_SILVER_SCHEMA = pl.Schema(
    {
        "observed_at_local": pl.Datetime(time_unit="us"),
        "observed_at_utc": pl.Datetime(time_unit="us", time_zone="UTC"),
        "timezone": pl.String,
        "transit_mode": pl.String,
        "station_complex_id": pl.String,
        "station_complex": pl.String,
        "borough": pl.String,
        "payment_method": pl.String,
        "fare_class_category": pl.String,
        "ridership": pl.Float64,
        "transfers": pl.Float64,
        "latitude": pl.Float64,
        "longitude": pl.Float64,
        "ingested_at": pl.Datetime(time_unit="us", time_zone="UTC"),
    }
)
SUBWAY_GRAIN_COLUMNS = (
    "observed_at_utc",
    "transit_mode",
    "station_complex_id",
    "payment_method",
    "fare_class_category",
)
SUBWAY_STRING_COLUMNS = (
    "transit_mode",
    "station_complex_id",
    "station_complex",
    "borough",
    "payment_method",
    "fare_class_category",
)


class SocrataPoint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["Point"]
    coordinates: tuple[Longitude, Latitude]


class _SubwayRidership(BaseModel):
    model_config = ConfigDict(extra="forbid")

    transit_mode: NonEmptyString
    station_complex_id: NonEmptyString
    station_complex: NonEmptyString
    borough: NonEmptyString
    payment_method: NonEmptyString
    fare_class_category: NonEmptyString
    ridership: NonNegativeFloat
    transfers: NonNegativeFloat
    latitude: Latitude
    longitude: Longitude

    @model_validator(mode="after")
    def ensure_transfers_do_not_exceed_ridership(self) -> Self:
        if self.transfers > self.ridership:
            raise ValueError("transfers must not exceed ridership")
        return self


class SubwaySourceRecord(_SubwayRidership):
    transit_timestamp: NaiveDateTime
    georeference: SocrataPoint | None = None

    @field_validator("transit_timestamp")
    @classmethod
    def ensure_timestamp_is_hourly(cls, value: datetime) -> datetime:
        if value.minute != 0 or value.second != 0 or value.microsecond != 0:
            raise ValueError("transit_timestamp must be rounded down to the hour")
        return value


class SubwayObservation(_SubwayRidership):
    observed_at_local: NaiveDateTime
    observed_at_utc: UTCDateTime
    timezone: NonEmptyString
    ingested_at: UTCDateTime
