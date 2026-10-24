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

active_flow_daily as (
    select
        date_day,
        sensor_id,
        flow_id,
        travel_mode,
        mobility_count,
        is_complete_day
    from {{ ref('active_mobility_weather_daily') }}
    where travel_mode in ('bike', 'pedestrian')
),

active_observed_daily as (
    select
        date_day,
        sum(mobility_count) filter (
            where travel_mode = 'bike'
        ) as bike_observed_count,
        count(distinct sensor_id) filter (
            where travel_mode = 'bike'
        ) as bike_reporting_sensors,
        sum(mobility_count) filter (
            where travel_mode = 'pedestrian'
        ) as pedestrian_observed_count,
        count(distinct sensor_id) filter (
            where travel_mode = 'pedestrian'
        ) as pedestrian_reporting_sensors
    from active_flow_daily
    group by date_day
),

active_expected_flows as (
    select
        sensor_id,
        travel_mode,
        count(distinct flow_id) as expected_flow_count
    from active_flow_daily
    group by
        sensor_id,
        travel_mode
),

active_sensor_daily as (
    select
        active_flow_daily.date_day,
        active_flow_daily.sensor_id as entity_id,
        active_flow_daily.travel_mode as activity_type,
        sum(active_flow_daily.mobility_count)::double precision
            as activity_value,
        count(distinct active_flow_daily.flow_id)
            = active_expected_flows.expected_flow_count
            and bool_and(active_flow_daily.is_complete_day)
            as is_complete_day
    from active_flow_daily
    inner join active_expected_flows
        on active_flow_daily.sensor_id = active_expected_flows.sensor_id
        and active_flow_daily.travel_mode = active_expected_flows.travel_mode
    group by
        active_flow_daily.date_day,
        active_flow_daily.sensor_id,
        active_flow_daily.travel_mode,
        active_expected_flows.expected_flow_count
),

subway_observed_daily as (
    select
        date_day,
        sum(total_ridership) as subway_total_ridership,
        count(distinct station_complex_id) as subway_reporting_stations
    from {{ ref('subway_weather_daily') }}
    group by date_day
),

subway_station_daily as (
    select
        date_day,
        station_complex_id as entity_id,
        'subway'::text as activity_type,
        total_ridership::double precision as activity_value,
        is_complete_day
    from {{ ref('subway_weather_daily') }}
),

entity_daily as (
    select
        date_day,
        entity_id,
        activity_type,
        activity_value,
        is_complete_day
    from active_sensor_daily

    union all

    select
        date_day,
        entity_id,
        activity_type,
        activity_value,
        is_complete_day
    from subway_station_daily
),

activity_periods as (
    select
        activity_type,
        min(date_day) as first_date,
        max(date_day) as last_date,
        (max(date_day) - min(date_day) + 1)::integer as period_day_count
    from entity_daily
    group by activity_type
),

entity_stats as (
    select
        entity_daily.activity_type,
        entity_daily.entity_id,
        activity_periods.period_day_count,
        count(*) filter (
            where entity_daily.is_complete_day
        ) as complete_day_count,
        avg(entity_daily.activity_value) filter (
            where entity_daily.is_complete_day
        ) as entity_baseline
    from entity_daily
    inner join activity_periods
        on entity_daily.activity_type = activity_periods.activity_type
    group by
        entity_daily.activity_type,
        entity_daily.entity_id,
        activity_periods.period_day_count
),

eligible_entities as (
    select
        activity_type,
        entity_id,
        entity_baseline
    from entity_stats
    where complete_day_count >= {{ var('activity_min_complete_days') }}
        and complete_day_count::numeric
            / nullif(period_day_count, 0)
            >= {{ var('activity_min_entity_coverage') }}
        and entity_baseline > 0
),

activity_calendar as (
    select
        dim_date.date_day,
        activity_periods.activity_type
    from {{ ref('dim_date') }} as dim_date
    inner join activity_periods
        on dim_date.date_day between activity_periods.first_date
            and activity_periods.last_date
),

daily_index_components as (
    select
        activity_calendar.date_day,
        activity_calendar.activity_type,
        count(eligible_entities.entity_id)::integer as eligible_entity_count,
        count(entity_daily.entity_id)::integer as complete_entity_count,
        avg(
            entity_daily.activity_value
            / nullif(eligible_entities.entity_baseline, 0)
        ) as relative_activity_mean
    from activity_calendar
    left join eligible_entities
        on activity_calendar.activity_type = eligible_entities.activity_type
    left join entity_daily
        on activity_calendar.date_day = entity_daily.date_day
        and eligible_entities.activity_type = entity_daily.activity_type
        and eligible_entities.entity_id = entity_daily.entity_id
        and entity_daily.is_complete_day
    group by
        activity_calendar.date_day,
        activity_calendar.activity_type
),

daily_indexes as (
    select
        date_day,
        activity_type,
        eligible_entity_count,
        complete_entity_count,
        complete_entity_count::double precision
            / nullif(eligible_entity_count, 0) as coverage_ratio,
        case
            when complete_entity_count::double precision
                / nullif(eligible_entity_count, 0)
                >= {{ var('activity_min_daily_coverage') }}
                then relative_activity_mean
        end as activity_index
    from daily_index_components
),

indexes_by_date as (
    select
        date_day,
        max(eligible_entity_count) filter (
            where activity_type = 'bike'
        ) as bike_eligible_sensors,
        max(complete_entity_count) filter (
            where activity_type = 'bike'
        ) as bike_complete_sensors,
        max(coverage_ratio) filter (
            where activity_type = 'bike'
        ) as bike_coverage_ratio,
        max(activity_index) filter (
            where activity_type = 'bike'
        ) as bike_activity_index,
        max(eligible_entity_count) filter (
            where activity_type = 'pedestrian'
        ) as pedestrian_eligible_sensors,
        max(complete_entity_count) filter (
            where activity_type = 'pedestrian'
        ) as pedestrian_complete_sensors,
        max(coverage_ratio) filter (
            where activity_type = 'pedestrian'
        ) as pedestrian_coverage_ratio,
        max(activity_index) filter (
            where activity_type = 'pedestrian'
        ) as pedestrian_activity_index,
        max(eligible_entity_count) filter (
            where activity_type = 'subway'
        ) as subway_eligible_stations,
        max(complete_entity_count) filter (
            where activity_type = 'subway'
        ) as subway_complete_stations,
        max(coverage_ratio) filter (
            where activity_type = 'subway'
        ) as subway_coverage_ratio,
        max(activity_index) filter (
            where activity_type = 'subway'
        ) as subway_activity_index
    from daily_indexes
    group by date_day
),

combined as (
    select
        weather_daily.date_day,
        weather_daily.avg_temperature_c,
        weather_daily.total_precipitation_mm,
        weather_daily.is_rainy_day,
        active_observed_daily.bike_observed_count,
        coalesce(active_observed_daily.bike_reporting_sensors, 0)
            as bike_reporting_sensors,
        coalesce(indexes_by_date.bike_eligible_sensors, 0)
            as bike_eligible_sensors,
        coalesce(indexes_by_date.bike_complete_sensors, 0)
            as bike_complete_sensors,
        indexes_by_date.bike_coverage_ratio,
        indexes_by_date.bike_activity_index,
        active_observed_daily.pedestrian_observed_count,
        coalesce(active_observed_daily.pedestrian_reporting_sensors, 0)
            as pedestrian_reporting_sensors,
        coalesce(indexes_by_date.pedestrian_eligible_sensors, 0)
            as pedestrian_eligible_sensors,
        coalesce(indexes_by_date.pedestrian_complete_sensors, 0)
            as pedestrian_complete_sensors,
        indexes_by_date.pedestrian_coverage_ratio,
        indexes_by_date.pedestrian_activity_index,
        subway_observed_daily.subway_total_ridership,
        coalesce(subway_observed_daily.subway_reporting_stations, 0)
            as subway_reporting_stations,
        coalesce(indexes_by_date.subway_eligible_stations, 0)
            as subway_eligible_stations,
        coalesce(indexes_by_date.subway_complete_stations, 0)
            as subway_complete_stations,
        indexes_by_date.subway_coverage_ratio,
        indexes_by_date.subway_activity_index
    from weather_daily
    left join active_observed_daily
        on weather_daily.date_day = active_observed_daily.date_day
    left join subway_observed_daily
        on weather_daily.date_day = subway_observed_daily.date_day
    left join indexes_by_date
        on weather_daily.date_day = indexes_by_date.date_day
)

select
    date_day,
    avg_temperature_c,
    total_precipitation_mm,
    is_rainy_day,
    bike_observed_count,
    bike_reporting_sensors,
    bike_eligible_sensors,
    bike_complete_sensors,
    bike_coverage_ratio,
    pedestrian_observed_count,
    pedestrian_reporting_sensors,
    pedestrian_eligible_sensors,
    pedestrian_complete_sensors,
    pedestrian_coverage_ratio,
    subway_total_ridership,
    subway_reporting_stations,
    subway_eligible_stations,
    subway_complete_stations,
    subway_coverage_ratio,
    bike_activity_index,
    pedestrian_activity_index,
    subway_activity_index
from combined
