select
    counter_id,
    observed_at_utc
from {{ ref('int_bike_counts_hourly') }}
group by
    counter_id,
    observed_at_utc
having count(*) > 1
