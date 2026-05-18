{{ config(
    materialized = 'table'
)}}


with signal_berth as(
  select signal_berth_id,station_id
  from {{ ref('dim_signal_berth')}}
  where station_id is not NULL
),locations as(
  select location_id,station_id
  from {{ref('dim_location')}}
  where station_id is not NULL
)

select
    {{ dbt_utils.generate_surrogate_key(['s.signal_berth_id', 'l.location_id']) }} as signal_location_bridge_id,
    signal_berth_id,
    location_id,
    true as is_active,
    current_timestamp() as dbt_updated_at
from signal_berth s 
join locations l on s.station_id = l.station_id