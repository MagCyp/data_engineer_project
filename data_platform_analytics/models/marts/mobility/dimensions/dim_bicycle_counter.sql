with source as (
    select
        counter_id,
        counter_name,
        domain_name,
        latitude,
        longitude,
        recording_interval_minutes,
        source_timezone,
        direction_detection_code,
        counter_serial_number
    from {{ ref('stg_mobility__bike_counters') }}
),

final as (
    select
        counter_id,
        counter_name,
        domain_name,
        latitude,
        longitude,
        recording_interval_minutes,
        source_timezone,
        direction_detection_code,
        counter_serial_number
    from source
)

select
    counter_id,
    counter_name,
    domain_name,
    latitude,
    longitude,
    recording_interval_minutes,
    source_timezone,
    direction_detection_code,
    counter_serial_number
from final
