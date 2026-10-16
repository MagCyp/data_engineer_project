from datetime import UTC, datetime
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

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

Latitude = Annotated[float, Field(ge=-90, le=90)]
Longitude = Annotated[float, Field(ge=-180, le=180)]
NonNegativeFloat = Annotated[float, Field(ge=0)]


class SocrataPoint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["Point"]
    coordinates: tuple[Longitude, Latitude]


class SubwaySourceRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    transit_timestamp: datetime
    transit_mode: str = Field(min_length=1)
    station_complex_id: str = Field(min_length=1)
    station_complex: str = Field(min_length=1)
    borough: str = Field(min_length=1)
    payment_method: str = Field(min_length=1)
    fare_class_category: str = Field(min_length=1)
    ridership: NonNegativeFloat
    transfers: NonNegativeFloat
    latitude: Latitude
    longitude: Longitude
    georeference: SocrataPoint | None = None

    @field_validator("transit_timestamp")
    @classmethod
    def ensure_local_hour_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is not None and value.utcoffset() is not None:
            raise ValueError("transit_timestamp must not contain a timezone")
        if value.minute != 0 or value.second != 0 or value.microsecond != 0:
            raise ValueError("transit_timestamp must be rounded down to the hour")
        return value

    @model_validator(mode="after")
    def ensure_transfers_do_not_exceed_ridership(self) -> Self:
        if self.transfers > self.ridership:
            raise ValueError("transfers must not exceed ridership")
        return self


class SubwayObservation(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    observed_at_local: datetime
    observed_at_utc: datetime
    transit_mode: str = Field(min_length=1)
    station_complex_id: str = Field(min_length=1)
    station_complex: str = Field(min_length=1)
    borough: str = Field(min_length=1)
    payment_method: str = Field(min_length=1)
    fare_class_category: str = Field(min_length=1)
    ridership: NonNegativeFloat
    transfers: NonNegativeFloat
    latitude: Latitude
    longitude: Longitude
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

    @model_validator(mode="after")
    def ensure_transfers_do_not_exceed_ridership(self) -> Self:
        if self.transfers > self.ridership:
            raise ValueError("transfers must not exceed ridership")
        return self
