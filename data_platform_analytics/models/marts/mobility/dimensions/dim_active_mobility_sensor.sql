select
    sensor_id,
    sensor_name,
    latitude,
    longitude,
    timezone,
    first_observed_at_local,
    last_observed_at_local,
    recording_interval_minutes,
    travel_modes,
    is_directional,
    has_timestamped_data,
    has_weather,
    operator_name
from {{ ref('stg_mobility__active_mobility_sensors') }}
