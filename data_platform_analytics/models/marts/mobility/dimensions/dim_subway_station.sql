with source as (
    select
        station_complex_id,
        station_complex,
        borough,
        latitude,
        longitude
    from {{ ref('stg_mobility__subway_ridership') }}
),

final as (
    select distinct
        station_complex_id,
        station_complex as station_complex_name,
        borough,
        latitude,
        longitude
    from source
)

select
    station_complex_id,
    station_complex_name,
    borough,
    latitude,
    longitude
from final
