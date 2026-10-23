with source as (
    select
        sensor_id,
        flow_id,
        travel_mode,
        direction,
        timezone,
        observed_at_local,
        observed_at_utc,
        interval_minutes,
        mobility_count,
        source_status,
        ingested_at
    from {{ ref('stg_mobility__active_mobility_counts') }}
),

hourly as (
    select
        sensor_id,
        flow_id,
        travel_mode,
        direction,
        date_trunc('hour', observed_at_local) as observed_at_local,
        date_trunc('hour', observed_at_utc, 'UTC') as observed_at_utc,
        timezone,
        interval_minutes,
        coalesce(
            sum(mobility_count) filter (
                where source_status in ('raw', 'modified')
            ),
            0
        ) as mobility_count,
        count(*) as source_record_count,
        count(*) filter (
            where source_status in ('raw', 'modified')
                and mobility_count is not null
        ) as valid_source_record_count,
        count(*) filter (
            where source_status = 'deleted'
                or mobility_count is null
        ) as problem_source_record_count,
        max(ingested_at) as latest_ingested_at
    from source
    group by
        sensor_id,
        flow_id,
        travel_mode,
        direction,
        date_trunc('hour', observed_at_local),
        date_trunc('hour', observed_at_utc, 'UTC'),
        timezone,
        interval_minutes
)

select
    sensor_id,
    flow_id,
    travel_mode,
    direction,
    observed_at_local,
    observed_at_utc,
    timezone,
    interval_minutes,
    mobility_count,
    source_record_count,
    valid_source_record_count,
    problem_source_record_count,
    latest_ingested_at
from hourly
