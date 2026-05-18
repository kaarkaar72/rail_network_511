with sch as(
  select 
    *,
    'schedule' as source_system
  from {{ ref('int_scheduled_tiploc') }}
  where station_id is not null
), tru as (
  select 
    *,
    'trust' as source_system
  from {{ref('int_trust_reference')}}
  where station_id is not null 
  and location_name is not null
),combined as( 
  select * from sch
  UNION ALL
  select * from tru
),ranked as (
  select *, 
    ROW_NUMBER() OVER (
      PARTITION BY station_id,tiploc_code
      ORDER BY
        case when source_system = 'trust' then 1 else 2 end
      ) as rn
  FROM combined 
), deduped as (
  select *
  FROM ranked
  where rn = 1
), area as (
  select *,
  CAST(LEFT(CAST(station_id as string),2) as integer) as geographical_id
  FROM deduped
)

SELECT *
FROM (
  SELECT
      {{ dbt_utils.generate_surrogate_key([
        'station_id', 'tiploc_code','nlc_code']) }} as location_id,
      station_id,
      geographical_id,
      tiploc_code,
      crs_code,
      nlc_code,
      location_name,
      source_system,
      current_timestamp() as dbt_updated_at,
      true as is_active
  from area
  UNION ALL
  SELECT
    {{ dbt_utils.generate_surrogate_key([
      "'Unknown'"
    ]) }} as location_id,
    -1 as station_id,
    -1 as geographical_id,
    "Unknown Tiploc Code" as tiploc_code,
    "Unknown CRS Code" as crs_code,
    -1 as nlc_code,
    "Unknown Location" as location_name,
    'system' as source_system,
    current_timestamp() as dbt_updated_at,
    false as is_active
)