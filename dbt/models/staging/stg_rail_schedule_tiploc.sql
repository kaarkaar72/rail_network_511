{{
  config(
    materialized = 'table',
    alias = 'stg_rail_schedule_tiploc'
  )
}}

with raw as (
    select *, 
    row_number() over (partition by json_extract_scalar(payload, '$.tiploc_code')  order by ingest_ts desc) as rn
    from {{ source('staging', 'rail_schedule_raw') }}
    where record_type = 'TiplocV1'
    {% if is_incremental() %}
        -- only scan today’s partition when running incrementally
        and date(ingest_ts) = current_date()
    {% endif %}
)

select
  -- Metadata
  cast(ingest_ts as timestamp) as ingest_ts,

  -- Core TIPLOC data
  json_extract_scalar(payload, '$.transaction_type') as transaction_type,
  json_extract_scalar(payload, '$.tiploc_code') as tiploc_code,
  CAST(json_extract_scalar(payload, '$.nalco') as integer) as nalco,
  CAST(json_extract_scalar(payload, '$.stanox') as integer) as stanox,
  CAST(json_extract_scalar(payload, '$.crs_code') as string) as crs_code,
  CAST(json_extract_scalar(payload, '$.description') as string) as  description,
  CAST(json_extract_scalar(payload, '$.tps_description') as string) as tps_description
from raw
where rn = 1
