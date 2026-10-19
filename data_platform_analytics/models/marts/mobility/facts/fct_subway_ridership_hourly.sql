with source as (
    select
        station_complex_id,
        transit_mode,
        observed_at_utc,
        ridership,
        transfers,
        payment_method_count,
        fare_class_category_count,
        source_record_count
    from {{ ref('int_subway_ridership_hourly') }}
),

final as (
    select
        station_complex_id,
        transit_mode,
        observed_at_utc,
        {{ to_mobility_date('observed_at_utc') }} as date_day,
        ridership,
        transfers,
        payment_method_count,
        fare_class_category_count,
        source_record_count
    from source
)

select
    station_complex_id,
    transit_mode,
    observed_at_utc,
    date_day,
    ridership,
    transfers,
    payment_method_count,
    fare_class_category_count,
    source_record_count
from final
