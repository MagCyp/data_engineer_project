select
    date_day,
    counter_id
from {{ ref('bike_weather_daily') }}
group by
    date_day,
    counter_id
having count(*) > 1
