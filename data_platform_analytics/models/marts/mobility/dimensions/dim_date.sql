with source_dates as (
    select {{ to_mobility_date('observed_at_utc') }} as date_day
    from {{ ref('stg_mobility__weather_observations') }}

    union all

    select {{ to_mobility_date('observed_at_utc') }} as date_day
    from {{ ref('stg_mobility__bike_counts') }}

    union all

    select {{ to_mobility_date('observed_at_utc') }} as date_day
    from {{ ref('stg_mobility__subway_ridership') }}
),

date_bounds as (
    select
        min(date_day) as min_date,
        max(date_day) as max_date
    from source_dates
),

date_spine as (
    select generate_series(min_date, max_date, interval '1 day')::date as date_day
    from date_bounds
),

final as (
    select
        date_day,
        extract(year from date_day)::smallint as year,
        extract(quarter from date_day)::smallint as quarter,
        extract(month from date_day)::smallint as month,
        trim(to_char(date_day, 'Month')) as month_name,
        extract(day from date_day)::smallint as day_of_month,
        extract(isodow from date_day)::smallint as day_of_week,
        extract(isodow from date_day) in (6, 7) as is_weekend,
        case
            when extract(month from date_day) in (12, 1, 2) then 'winter'
            when extract(month from date_day) in (3, 4, 5) then 'spring'
            when extract(month from date_day) in (6, 7, 8) then 'summer'
            else 'autumn'
        end as season,
        (
            extract(
                epoch from (
                    (date_day + 1)::timestamp
                        at time zone '{{ var("mobility_timezone") }}'
                    - date_day::timestamp
                        at time zone '{{ var("mobility_timezone") }}'
                )
            ) / 3600
        )::smallint as expected_hour_count
    from date_spine
)

select
    date_day,
    year,
    quarter,
    month,
    month_name,
    day_of_month,
    day_of_week,
    is_weekend,
    season,
    expected_hour_count
from final
