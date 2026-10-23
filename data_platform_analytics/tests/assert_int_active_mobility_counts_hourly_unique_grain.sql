select
    flow_id,
    observed_at_utc
from {{ ref('int_active_mobility_counts_hourly') }}
group by
    flow_id,
    observed_at_utc
having count(*) > 1
