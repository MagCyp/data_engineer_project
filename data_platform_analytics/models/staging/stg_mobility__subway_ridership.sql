select
    observed_at_local,
    observed_at_utc,
    timezone,
    transit_mode,
    station_complex_id,
    station_complex,
    borough,
    payment_method,
    fare_class_category,
    ridership,
    transfers,
    latitude,
    longitude,
    ingested_at
from {{ source('mobility', 'subway_ridership') }}
