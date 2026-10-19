with source as (
    select
        counter_id,
        observed_at_utc,
        bike_count,
        source_record_count,
        valid_source_record_count,
        problem_source_record_count,
        latest_ingested_at
    from {{ ref('int_bike_counts_hourly') }}
),

final as (
    select
        counter_id,
        observed_at_utc,
        {{ to_mobility_date('observed_at_utc') }} as date_day,
        bike_count,
        source_record_count,
        valid_source_record_count,
        problem_source_record_count,
        (60 / {{ var('bike_count_interval_minutes') }})::smallint
            as expected_record_count,
        valid_source_record_count = (60 / {{ var('bike_count_interval_minutes') }})
            and problem_source_record_count = 0 as is_complete_hour,
        latest_ingested_at
    from source
)

select
    counter_id,
    observed_at_utc,
    date_day,
    bike_count,
    source_record_count,
    valid_source_record_count,
    problem_source_record_count,
    expected_record_count,
    is_complete_hour,
    latest_ingested_at
from final
