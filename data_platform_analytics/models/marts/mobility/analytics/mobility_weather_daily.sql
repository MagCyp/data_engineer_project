with weather_daily as (
    select
        date_day,
        avg(temperature_c) as avg_temperature_c,
        sum(precipitation_mm) as total_precipitation_mm,
        sum(rain_mm) > {{ var('rainy_day_threshold_mm') }} as is_rainy_day
    from {{ ref('fct_weather_hourly') }}
    where location = '{{ var("mobility_weather_location") }}'
    group by date_day
),

bicycle_daily as (
    select
        date_day,
        sum(bike_count) as bike_observed_count,
        count(distinct counter_id) as bike_reporting_sensors
    from {{ ref('bike_weather_daily') }}
    group by date_day
),

subway_daily as (
    select
        date_day,
        sum(total_ridership) as subway_total_ridership,
        count(distinct station_complex_id) as subway_reporting_stations
    from {{ ref('subway_weather_daily') }}
    group by date_day
),

combined as (
    select
        weather_daily.date_day,
        weather_daily.avg_temperature_c,
        weather_daily.total_precipitation_mm,
        weather_daily.is_rainy_day,
        bicycle_daily.bike_observed_count,
        coalesce(bicycle_daily.bike_reporting_sensors, 0)
            as bike_reporting_sensors,
        subway_daily.subway_total_ridership,
        coalesce(subway_daily.subway_reporting_stations, 0)
            as subway_reporting_stations
    from weather_daily
    left join bicycle_daily
        on weather_daily.date_day = bicycle_daily.date_day
    left join subway_daily
        on weather_daily.date_day = subway_daily.date_day
),

final as (
    select
        date_day,
        avg_temperature_c,
        total_precipitation_mm,
        is_rainy_day,
        bike_observed_count,
        bike_reporting_sensors,
        subway_total_ridership,
        subway_reporting_stations,
        bike_observed_count
            / nullif(avg(bike_observed_count) over (), 0)
            as bike_activity_index,
        subway_total_ridership
            / nullif(avg(subway_total_ridership) over (), 0)
            as subway_activity_index
    from combined
)

select
    date_day,
    avg_temperature_c,
    total_precipitation_mm,
    is_rainy_day,
    bike_observed_count,
    bike_reporting_sensors,
    subway_total_ridership,
    subway_reporting_stations,
    bike_activity_index,
    subway_activity_index
from final
