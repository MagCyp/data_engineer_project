with source as (
    select
        counter_id,
        timezone,
        observed_at_local,
        observed_at_utc,
        bike_count,
        ingested_at
    from {{ ref('stg_mobility__bike_counts') }}
),

hourly as (
    select
        counter_id,
        date_trunc('hour', observed_at_local) as observed_at_local,
        date_trunc('hour', observed_at_utc, 'UTC') as observed_at_utc,
        timezone,
        sum(bike_count) as bike_count,
        count(*) as source_record_count,
        max(ingested_at) as latest_ingested_at
    from source
    group by
        counter_id,
        date_trunc('hour', observed_at_local),
        date_trunc('hour', observed_at_utc, 'UTC'),
        timezone
),

final as (
    select
        counter_id,
        observed_at_local,
        observed_at_utc,
        timezone,
        bike_count,
        source_record_count,
        latest_ingested_at
    from hourly
)

select
    counter_id,
    observed_at_local,
    observed_at_utc,
    timezone,
    bike_count,
    source_record_count,
    latest_ingested_at
from final
