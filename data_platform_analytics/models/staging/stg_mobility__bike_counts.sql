select
    record_id,
    counter_id,
    timezone,
    observed_at_local,
    observed_at_utc,
    bike_count,
    status,
    ingested_at
from {{ source('mobility', 'bike_counts') }}
