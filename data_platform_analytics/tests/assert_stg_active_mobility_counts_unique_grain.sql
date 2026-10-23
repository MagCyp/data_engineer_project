select
    flow_id,
    observed_at_utc,
    interval_minutes
from {{ ref('stg_mobility__active_mobility_counts') }}
group by
    flow_id,
    observed_at_utc,
    interval_minutes
having count(*) > 1
