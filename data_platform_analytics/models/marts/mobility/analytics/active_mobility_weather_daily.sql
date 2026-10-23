with mobility_counts as (
    select
        date_day,
        sensor_id,
        flow_id,
        travel_mode,
        mobility_count,
        is_complete_hour
    from {{ ref('fct_active_mobility_counts_hourly') }}
),

mobility_daily as (
    select
        date_day,
        sensor_id,
        flow_id,
        travel_mode,
        sum(mobility_count) as mobility_count,
        count(*) filter (where is_complete_hour) as valid_hours
    from mobility_counts
    group by
        date_day,
        sensor_id,
        flow_id,
        travel_mode
),

weather_daily as (
    select
        date_day,
        avg(temperature_c) as avg_temperature_c,
        sum(precipitation_mm) as total_precipitation_mm,
        avg(wind_speed_kmh) as avg_wind_speed_kmh,
        sum(rain_mm) > {{ var('rainy_day_threshold_mm') }} as is_rainy_day
    from {{ ref('fct_weather_hourly') }}
    where location = '{{ var("mobility_weather_location") }}'
    group by date_day
)

select
    mobility_daily.date_day,
    mobility_daily.sensor_id,
    mobility_daily.flow_id,
    mobility_daily.travel_mode,
    mobility_daily.mobility_count,
    mobility_daily.valid_hours,
    mobility_daily.valid_hours = dim_date.expected_hour_count
        as is_complete_day,
    weather_daily.avg_temperature_c,
    weather_daily.total_precipitation_mm,
    weather_daily.avg_wind_speed_kmh,
    weather_daily.is_rainy_day
from mobility_daily
inner join {{ ref('dim_date') }} as dim_date
    on mobility_daily.date_day = dim_date.date_day
left join weather_daily
    on mobility_daily.date_day = weather_daily.date_day
