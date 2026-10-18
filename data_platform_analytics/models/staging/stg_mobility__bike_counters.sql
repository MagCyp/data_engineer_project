with source as (
    select
        id,
        name,
        domain,
        latitude,
        longitude,
        interval,
        timezone,
        sens,
        counter
    from {{ ref('bicycle_counters') }}
),

renamed as (
    select
        id as counter_id,
        name as counter_name,
        domain as domain_name,
        latitude as latitude_raw,
        longitude as longitude_raw,
        interval as recording_interval_minutes,
        timezone as source_timezone,
        sens as direction_detection_code,
        counter as counter_serial_number
    from source
),

final as (
    select
        counter_id,
        counter_name,
        domain_name,
        {{ decimal_comma_to_numeric('latitude_raw') }} as latitude,
        {{ decimal_comma_to_numeric('longitude_raw') }} as longitude,
        recording_interval_minutes,
        source_timezone,
        direction_detection_code,
        counter_serial_number
    from renamed
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
