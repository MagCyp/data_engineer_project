with hourly_totals as (
    select
        date_day,
        sensor_id,
        flow_id,
        travel_mode,
        sum(mobility_count) as mobility_count
    from {{ ref('fct_active_mobility_counts_hourly') }}
    group by
        date_day,
        sensor_id,
        flow_id,
        travel_mode
),

daily_totals as (
    select
        date_day,
        sensor_id,
        flow_id,
        travel_mode,
        mobility_count
    from {{ ref('active_mobility_weather_daily') }}
)

select
    coalesce(hourly_totals.date_day, daily_totals.date_day) as date_day,
    coalesce(hourly_totals.sensor_id, daily_totals.sensor_id) as sensor_id,
    coalesce(hourly_totals.flow_id, daily_totals.flow_id) as flow_id,
    coalesce(hourly_totals.travel_mode, daily_totals.travel_mode) as travel_mode,
    hourly_totals.mobility_count as hourly_mobility_count,
    daily_totals.mobility_count as daily_mobility_count
from hourly_totals
full outer join daily_totals
    on hourly_totals.date_day = daily_totals.date_day
    and hourly_totals.sensor_id = daily_totals.sensor_id
    and hourly_totals.flow_id = daily_totals.flow_id
    and hourly_totals.travel_mode = daily_totals.travel_mode
where hourly_totals.mobility_count
    is distinct from daily_totals.mobility_count
