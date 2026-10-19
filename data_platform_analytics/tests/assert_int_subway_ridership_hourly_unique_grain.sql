select
    station_complex_id,
    transit_mode,
    observed_at_utc
from {{ ref('int_subway_ridership_hourly') }}
group by
    station_complex_id,
    transit_mode,
    observed_at_utc
having count(*) > 1
