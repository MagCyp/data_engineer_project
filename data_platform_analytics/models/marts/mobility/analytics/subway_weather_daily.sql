with subway_ridership as (
    select
        date_day,
        station_complex_id,
        observed_at_utc,
        ridership,
        transfers
    from {{ ref('fct_subway_ridership_hourly') }}
),

subway_daily as (
    select
        date_day,
        station_complex_id,
        sum(ridership) as total_ridership,
        sum(transfers) as total_transfers,
        count(distinct observed_at_utc) as observed_hours
    from subway_ridership
    group by
        date_day,
        station_complex_id
),

weather_daily as (
    select
        date_day,
        avg(temperature_c) as avg_temperature_c,
        sum(precipitation_mm) as total_precipitation_mm,
        sum(rain_mm) > {{ var('rainy_day_threshold_mm') }} as is_rainy_day
    from {{ ref('fct_weather_hourly') }}
    where location = '{{ var("mobility_weather_location") }}'
    group by date_day
),

final as (
    select
        subway_daily.date_day,
        subway_daily.station_complex_id,
        dim_subway_station.borough,
        subway_daily.total_ridership,
        subway_daily.total_transfers,
        subway_daily.observed_hours,
        subway_daily.observed_hours = dim_date.expected_hour_count
            as is_complete_day,
        weather_daily.avg_temperature_c,
        weather_daily.total_precipitation_mm,
        weather_daily.is_rainy_day
    from subway_daily
    left join {{ ref('dim_date') }} as dim_date
        on subway_daily.date_day = dim_date.date_day
    left join {{ ref('dim_subway_station') }} as dim_subway_station
        on subway_daily.station_complex_id
            = dim_subway_station.station_complex_id
    left join weather_daily
        on subway_daily.date_day = weather_daily.date_day
)

select
    date_day,
    station_complex_id,
    borough,
    total_ridership,
    total_transfers,
    observed_hours,
    is_complete_day,
    avg_temperature_c,
    total_precipitation_mm,
    is_rainy_day
from final
