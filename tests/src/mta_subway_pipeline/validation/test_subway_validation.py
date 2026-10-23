from datetime import UTC, datetime

import polars as pl
import pytest

from mta_subway_pipeline.transformations import (
    transform_bronze_to_silver,
    transform_source_to_bronze,
)
from mta_subway_pipeline.validation import (
    SUBWAY_SILVER_SCHEMA,
    SubwaySourceRecord,
    validate_bronze_subway,
    validate_silver_subway,
)


def source_record() -> SubwaySourceRecord:
    return SubwaySourceRecord(
        transit_timestamp=datetime(2025, 1, 15, 8),
        transit_mode="subway",
        station_complex_id="158",
        station_complex="86 St (C,B)",
        borough="Manhattan",
        payment_method="omny",
        fare_class_category="OMNY - Full Fare",
        ridership=451.0,
        transfers=26.0,
        latitude=40.78587,
        longitude=-73.96892,
        georeference={
            "type": "Point",
            "coordinates": (-73.96892, 40.78587),
        },
    )


def silver_dataframe() -> pl.DataFrame:
    bronze = transform_source_to_bronze(
        [source_record()],
        ingested_at=datetime(2026, 10, 18, 12, tzinfo=UTC),
    )
    return transform_bronze_to_silver(bronze)


def test_validate_bronze_subway_accepts_valid_data() -> None:
    bronze = transform_source_to_bronze(
        [source_record()],
        ingested_at=datetime(2026, 10, 18, 12, tzinfo=UTC),
    )

    assert validate_bronze_subway(bronze) is bronze


def test_validate_bronze_subway_rejects_invalid_measure() -> None:
    bronze = transform_source_to_bronze(
        [source_record()],
        ingested_at=datetime(2026, 10, 18, 12, tzinfo=UTC),
    ).with_columns(pl.lit(-1.0).alias("ridership"))

    with pytest.raises(ValueError, match="failed for 1 row"):
        validate_bronze_subway(bronze)


def test_subway_validation_preserves_negative_transfer_estimate() -> None:
    bronze = transform_source_to_bronze(
        [source_record().model_copy(update={"transfers": -1.0})],
        ingested_at=datetime(2026, 10, 18, 12, tzinfo=UTC),
    )

    validate_bronze_subway(bronze)
    silver = transform_bronze_to_silver(bronze)

    assert silver.item(0, "transfers") == -1.0
    assert validate_silver_subway(silver) is silver


def test_validate_silver_subway_rejects_duplicate_grain() -> None:
    silver = pl.concat([silver_dataframe(), silver_dataframe()]).cast(
        SUBWAY_SILVER_SCHEMA
    )

    with pytest.raises(ValueError, match="duplicate grain"):
        validate_silver_subway(silver)
