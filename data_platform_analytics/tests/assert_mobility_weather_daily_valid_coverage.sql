select
    date_day,
    bike_eligible_sensors,
    bike_complete_sensors,
    bike_coverage_ratio,
    bike_activity_index,
    pedestrian_eligible_sensors,
    pedestrian_complete_sensors,
    pedestrian_coverage_ratio,
    pedestrian_activity_index,
    subway_eligible_stations,
    subway_complete_stations,
    subway_coverage_ratio,
    subway_activity_index
from {{ ref('mobility_weather_daily') }}
where bike_complete_sensors > bike_eligible_sensors
    or pedestrian_complete_sensors > pedestrian_eligible_sensors
    or subway_complete_stations > subway_eligible_stations
    or bike_coverage_ratio not between 0 and 1
    or pedestrian_coverage_ratio not between 0 and 1
    or subway_coverage_ratio not between 0 and 1
    or (
        bike_activity_index is not null
        and coalesce(bike_coverage_ratio, 0)
            < {{ var('activity_min_daily_coverage') }}
    )
    or (
        pedestrian_activity_index is not null
        and coalesce(pedestrian_coverage_ratio, 0)
            < {{ var('activity_min_daily_coverage') }}
    )
    or (
        subway_activity_index is not null
        and coalesce(subway_coverage_ratio, 0)
            < {{ var('activity_min_daily_coverage') }}
    )
