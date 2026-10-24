{{ config(severity='warn') }}

with ordered_observations as (
    select
        counts.sensor_id,
        counts.flow_id,
        (counts.observed_at_utc at time zone 'UTC')::date as date_day_utc,
        counts.observed_at_utc,
        counts.interval_minutes,
        sensors.recording_interval_minutes,
        extract(
            epoch from (
                counts.observed_at_utc
                - lag(counts.observed_at_utc) over (
                    partition by
                        counts.flow_id,
                        (counts.observed_at_utc at time zone 'UTC')::date
                    order by counts.observed_at_utc
                )
            )
        ) / 60 as gap_minutes
    from {{ ref('stg_mobility__active_mobility_counts') }} as counts
    inner join {{ ref('stg_mobility__active_mobility_sensors') }} as sensors
        on counts.sensor_id = sensors.sensor_id
),

sensor_days as (
    select
        sensor_id,
        date_day_utc,
        count(*) filter (
            where interval_minutes <> recording_interval_minutes
        ) as metadata_interval_mismatch_count,
        coalesce(
            sum(
                greatest(
                    floor(gap_minutes / interval_minutes)::integer - 1,
                    0
                )
            ) filter (where gap_minutes is not null),
            0
        ) as missing_interval_count
    from ordered_observations
    group by
        sensor_id,
        date_day_utc
)

select
    sensor_id,
    date_day_utc,
    metadata_interval_mismatch_count,
    missing_interval_count
from sensor_days
where metadata_interval_mismatch_count > 0
    or missing_interval_count > 1
