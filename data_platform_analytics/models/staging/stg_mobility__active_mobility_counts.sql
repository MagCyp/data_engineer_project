select
    sensor_id,
    flow_id,
    flow_name,
    travel_mode,
    direction,
    timezone,
    observed_at_local,
    observed_at_utc,
    interval_minutes,
    mobility_count,
    source_status,
    ingested_at
from {{ source('mobility', 'active_mobility_counts') }}
