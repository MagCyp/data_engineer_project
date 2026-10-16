from datetime import datetime
from typing import Literal, Self

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
SUBWAY_SOURCE_FIELDS = (
    "transit_timestamp",
    "transit_mode",
    "station_complex_id",
    "station_complex",
    "borough",
    "payment_method",
    "fare_class_category",
    "ridership",
    "transfers",
    "latitude",
    "longitude",
    "georeference",
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
    ingested_at: UTCDateTime
