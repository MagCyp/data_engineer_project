with source as (
    select
        observed_at_utc,
        transit_mode,
        station_complex_id,
        payment_method,
        fare_class_category,
        ridership,
        transfers,
        ingested_at
    from {{ ref('stg_mobility__subway_ridership') }}
),

hourly as (
    select
        station_complex_id,
        transit_mode,
        observed_at_utc,
        sum(ridership) as ridership,
        sum(transfers) as transfers,
        count(distinct payment_method) as payment_method_count,
        count(distinct fare_class_category) as fare_class_category_count,
        count(*) as source_record_count,
        max(ingested_at) as latest_ingested_at
    from source
    group by
        station_complex_id,
        transit_mode,
        observed_at_utc
),

final as (
    select
        station_complex_id,
        transit_mode,
        observed_at_utc,
        ridership,
        transfers,
        payment_method_count,
        fare_class_category_count,
        source_record_count,
        latest_ingested_at
    from hourly
)

select
    station_complex_id,
    transit_mode,
    observed_at_utc,
    ridership,
    transfers,
    payment_method_count,
    fare_class_category_count,
    source_record_count,
    latest_ingested_at
from final
