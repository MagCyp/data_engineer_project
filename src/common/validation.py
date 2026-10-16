from datetime import UTC, datetime
from typing import Annotated

from pydantic import AfterValidator, Field, StringConstraints


def ensure_naive_datetime(value: datetime) -> datetime:
    if value.tzinfo is not None and value.utcoffset() is not None:
        raise ValueError("local timestamps must not contain a timezone")
    return value


def normalize_utc_datetime(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("UTC timestamps must be timezone-aware")
    return value.astimezone(UTC)


Latitude = Annotated[float, Field(ge=-90, le=90)]
Longitude = Annotated[float, Field(ge=-180, le=180)]
NaiveDateTime = Annotated[datetime, AfterValidator(ensure_naive_datetime)]
NonEmptyString = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1),
]
NonNegativeFloat = Annotated[float, Field(ge=0)]
NonNegativeInt = Annotated[int, Field(ge=0)]
Percentage = Annotated[int, Field(ge=0, le=100)]
PositiveInt = Annotated[int, Field(gt=0)]
UTCDateTime = Annotated[datetime, AfterValidator(normalize_utc_datetime)]
