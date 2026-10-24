with hourly_totals as (
    select
        date_day,
        station_complex_id,
        sum(ridership) as total_ridership,
        sum(transfers) as total_transfers
    from {{ ref('fct_subway_ridership_hourly') }}
    group by
        date_day,
        station_complex_id
),

daily_totals as (
    select
        date_day,
        station_complex_id,
        total_ridership,
        total_transfers
    from {{ ref('subway_weather_daily') }}
)

select
    coalesce(hourly_totals.date_day, daily_totals.date_day) as date_day,
    coalesce(
        hourly_totals.station_complex_id,
        daily_totals.station_complex_id
    ) as station_complex_id,
    hourly_totals.total_ridership as hourly_ridership,
    daily_totals.total_ridership as daily_ridership,
    hourly_totals.total_transfers as hourly_transfers,
    daily_totals.total_transfers as daily_transfers
from hourly_totals
full outer join daily_totals
    on hourly_totals.date_day = daily_totals.date_day
    and hourly_totals.station_complex_id = daily_totals.station_complex_id
where hourly_totals.total_ridership
        is distinct from daily_totals.total_ridership
    or hourly_totals.total_transfers
        is distinct from daily_totals.total_transfers
