select
    location,
    timezone,
    observed_at_utc,
    temperature_c,
    relative_humidity_pct,
    precipitation_mm,
    rain_mm,
    wind_speed_kmh,
    ingested_at
from {{ source('mobility', 'weather_observations') }}
