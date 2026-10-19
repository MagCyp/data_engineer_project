with bicycle_counts as (
    select
        date_day,
        counter_id,
        bike_count,
        is_complete_hour
    from {{ ref('fct_bicycle_counts_hourly') }}
),

bicycle_daily as (
    select
        date_day,
        counter_id,
        sum(bike_count) as bike_count,
        count(*) filter (where is_complete_hour) as valid_hours
    from bicycle_counts
    group by
        date_day,
        counter_id
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
),

final as (
    select
        bicycle_daily.date_day,
        bicycle_daily.counter_id,
        bicycle_daily.bike_count,
        bicycle_daily.valid_hours,
        bicycle_daily.valid_hours = dim_date.expected_hour_count
            as is_complete_day,
        weather_daily.avg_temperature_c,
        weather_daily.total_precipitation_mm,
        weather_daily.avg_wind_speed_kmh,
        weather_daily.is_rainy_day
    from bicycle_daily
    inner join {{ ref('dim_date') }} as dim_date
        on bicycle_daily.date_day = dim_date.date_day
    left join weather_daily
        on bicycle_daily.date_day = weather_daily.date_day
)

select
    date_day,
    counter_id,
    bike_count,
    valid_hours,
    is_complete_day,
    avg_temperature_c,
    total_precipitation_mm,
    avg_wind_speed_kmh,
    is_rainy_day
from final
