with source as (
    select
        location,
        observed_at_utc,
        temperature_c,
        relative_humidity_pct,
        precipitation_mm,
        rain_mm,
        wind_speed_kmh
    from {{ ref('stg_mobility__weather_observations') }}
),

final as (
    select
        location,
        observed_at_utc,
        {{ to_mobility_date('observed_at_utc') }} as date_day,
        temperature_c,
        relative_humidity_pct,
        precipitation_mm,
        rain_mm,
        wind_speed_kmh
    from source
)

select
    location,
    observed_at_utc,
    date_day,
    temperature_c,
    relative_humidity_pct,
    precipitation_mm,
    rain_mm,
    wind_speed_kmh
from final
