with source as (
    select
        observed_at_local,
        observed_at_utc,
        timezone,
        transit_mode,
        station_complex_id,
        station_complex,
        borough,
        payment_method,
        fare_class_category,
        ridership,
        transfers,
        latitude,
        longitude,
        ingested_at
    from {{ ref('stg_mobility__subway_ridership') }}
),

hourly as (
    select
        observed_at_local,
        observed_at_utc,
        timezone,
        transit_mode,
        station_complex_id,
        station_complex,
        borough,
        latitude,
        longitude,
        sum(ridership) as ridership,
        sum(transfers) as transfers,
        count(distinct payment_method) as payment_method_count,
        count(distinct fare_class_category) as fare_class_category_count,
        count(*) as source_record_count,
        max(ingested_at) as latest_ingested_at
    from source
    group by
        observed_at_local,
        observed_at_utc,
        timezone,
        transit_mode,
        station_complex_id,
        station_complex,
        borough,
        latitude,
        longitude
),

final as (
    select
        observed_at_local,
        observed_at_utc,
        timezone,
        transit_mode,
        station_complex_id,
        station_complex,
        borough,
        latitude,
        longitude,
        ridership,
        transfers,
        payment_method_count,
        fare_class_category_count,
        source_record_count,
        latest_ingested_at
    from hourly
)

select
    observed_at_local,
    observed_at_utc,
    timezone,
    transit_mode,
    station_complex_id,
    station_complex,
    borough,
    latitude,
    longitude,
    ridership,
    transfers,
    payment_method_count,
    fare_class_category_count,
    source_record_count,
    latest_ingested_at
from final
