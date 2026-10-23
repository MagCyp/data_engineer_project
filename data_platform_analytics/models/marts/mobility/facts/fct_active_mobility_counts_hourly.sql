with source as (
    select
        sensor_id,
        flow_id,
        travel_mode,
        direction,
        observed_at_utc,
        interval_minutes,
        mobility_count,
        source_record_count,
        valid_source_record_count,
        problem_source_record_count,
        latest_ingested_at
    from {{ ref('int_active_mobility_counts_hourly') }}
)

select
    sensor_id,
    flow_id,
    travel_mode,
    direction,
    observed_at_utc,
    {{ to_mobility_date('observed_at_utc') }} as date_day,
    interval_minutes,
    mobility_count,
    source_record_count,
    valid_source_record_count,
    problem_source_record_count,
    (60 / interval_minutes)::smallint as expected_record_count,
    valid_source_record_count = (60 / interval_minutes)
        and source_record_count = (60 / interval_minutes)
        and problem_source_record_count = 0 as is_complete_hour,
    latest_ingested_at
from source
