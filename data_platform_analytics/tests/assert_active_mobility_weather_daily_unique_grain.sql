select
    date_day,
    flow_id,
    travel_mode
from {{ ref('active_mobility_weather_daily') }}
group by
    date_day,
    flow_id,
    travel_mode
having count(*) > 1
