{{ 
  config(
    materialized='table'
    ) 
  }}


SELECT * 
FROM (
  SELECT
  {{ dbt_utils.generate_surrogate_key([
        'stanox','td','from_berth','to_berth','step_type','route'
    ]) }} as signal_berth_id,
  CAST(td as string) as area_id,
  CAST(stanox as integer) as station_id,   
  CAST(stanme as string) as station_name,             
  CAST(step_type as string) as step_type,
  CAST(from_berth as string) as from_berth, 
  CAST(to_berth as string) as to_berth,
  CAST(berth_offset as integer) as berth_offset,
  CAST(event as string) as event,
  CAST(platform as integer) as platform,
  CAST(from_line as string) as from_line,
  CAST(to_line as string) as to_line, 
  CAST(route as integer) as route,
  CAST(comment as string) as comment,
  true as is_active,
  current_timestamp() as dbt_updated_at
from {{ ref('td_smart') }}
where td is not null
UNION ALL
SELECT 
{{ dbt_utils.generate_surrogate_key([
    "'Unknown'"
]) }} as signal_berth_id,
null as area_id,
null as station_id,   
null as station_name,             
null as step_type,
null as from_berth, 
null as to_berth,
null as berth_offset,
null as event,
null as platform,
null as from_line,
null as to_line, 
null as route,
null as comment,
true as is_active,
current_timestamp() as dbt_updated_at
)

