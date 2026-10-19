with source as (
    select
        counter_id,
        timezone,
        observed_at_local,
        observed_at_utc,
        bike_count,
        status,
        ingested_at
    from {{ ref('stg_mobility__bike_counts') }}
),

hourly as (
    select
        counter_id,
        date_trunc('hour', observed_at_local) as observed_at_local,
        date_trunc('hour', observed_at_utc, 'UTC') as observed_at_utc,
        timezone,
        sum(
            case
                when status in ({{ var('bike_valid_statuses') | join(', ') }})
                    then bike_count
                else 0
            end
        ) as bike_count,
        count(*) as source_record_count,
        count(*) filter (
            where status in ({{ var('bike_valid_statuses') | join(', ') }})
        ) as valid_source_record_count,
        count(*) filter (
            where status not in ({{ var('bike_valid_statuses') | join(', ') }})
        ) as problem_source_record_count,
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
        valid_source_record_count,
        problem_source_record_count,
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
    valid_source_record_count,
    problem_source_record_count,
    latest_ingested_at
from final
