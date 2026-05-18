{{ 
  config(
    materialized='table'
    ) 
  }}

SELECT
  {{ dbt_utils.generate_surrogate_key([
        'area_id','name',
    ]) }} as td_area_id,
  CAST(area_id as string) as area_id,
  CAST(name as string) as area_name,
  CAST(sig as boolean) as signal_aspects,
  CAST(rte as boolean) as route_set_indications,
  CAST(lat as boolean) as latch_indications,
  CAST(trk as boolean) as track_occupation_indicator,
  CAST(pts as boolean) as points_indicator,
  CAST(lxg as boolean) as level_crossing_barrier_indicator,
  true as is_active,
  current_timestamp() as dbt_updated_at
from {{ ref('td_area') }}
where area_id is not null

