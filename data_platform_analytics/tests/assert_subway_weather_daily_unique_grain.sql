select
    date_day,
    station_complex_id
from {{ ref('subway_weather_daily') }}
group by
    date_day,
    station_complex_id
having count(*) > 1
