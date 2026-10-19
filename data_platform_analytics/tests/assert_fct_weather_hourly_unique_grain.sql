select
    location,
    observed_at_utc
from {{ ref('fct_weather_hourly') }}
group by
    location,
    observed_at_utc
having count(*) > 1
