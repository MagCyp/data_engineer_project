select
    location,
    observed_at_utc,
    count(*) as row_count
from {{ ref('stg_mobility__weather_observations') }}
group by
    location,
    observed_at_utc
having count(*) > 1