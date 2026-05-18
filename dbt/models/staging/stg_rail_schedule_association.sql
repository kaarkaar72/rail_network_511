{{
    config(
        alias = 'stg_rail_schedule_assciation',
        materialized = 'incremental',
        unique_key= 'association_id',
        incremental_strategy = "insert_overwrite",
        partition_by = {
            "field": "ingest_ts",
            "data_type": "timestamp",
            "granularity": "day"
        },
        cluster_by=['main_train_uid','assoc_train_uid','assoc_start_date','assoc_end_date']
    )
}}

with raw as (
  select *,
    row_number() over
    (partition by 
      json_extract_scalar(payload, '$.main_train_uid'),
      json_extract_scalar(payload,'$.assoc_train_uid'),
      json_extract_scalar(payload,'$.assoc_start_date'),
      json_extract_scalar(payload,'$.assoc_end_date'),
      json_extract_scalar(payload,'$.category'),
      json_extract_scalar(payload, '$.location'),
      json_extract_scalar(payload, '$.CIF_stp_indicator')
    order by    
      ingest_ts DESC) as rn
  from {{ source('staging', 'rail_schedule_raw') }}
  where record_type = 'JsonAssociationV1'
  {% if is_incremental() %}
    -- only scan today’s partition when running incrementally
    and date(ingest_ts) = current_date()
  {% endif %}
)

select
  -- Metadata
  cast(ingest_ts as timestamp) as ingest_ts,
  {{ dbt_utils.generate_surrogate_key([
    "json_extract_scalar(payload, '$.main_train_uid')",
    "json_extract_scalar(payload, '$.assoc_train_uid')",
    "json_extract_scalar(payload, '$.assoc_start_date')",
    "json_extract_scalar(payload, '$.assoc_end_date')",
    "json_extract_scalar(payload, '$.location')",
    "json_extract_scalar(payload, '$.category')",
    "json_extract_scalar(payload, '$.CIF_stp_indicator')"
  ]) }} as association_id,

  -- Core association details
  json_extract_scalar(payload, '$.transaction_type') as transaction_type,
  json_extract_scalar(payload, '$.main_train_uid') as main_train_uid,
  json_extract_scalar(payload, '$.assoc_train_uid') as assoc_train_uid,
  CAST(timestamp(json_extract_scalar(payload, '$.assoc_start_date')) as date) as assoc_start_date,
  CAST(timestamp(json_extract_scalar(payload, '$.assoc_end_date')) as date) as assoc_end_date,
  json_extract_scalar(payload, '$.assoc_days') as assoc_days,
  json_extract_scalar(payload, '$.category') as assoc_category,
  json_extract_scalar(payload, '$.date_indicator') as date_indicator,
  json_extract_scalar(payload, '$.location') as assoc_location,
  json_extract_scalar(payload, '$.base_location_suffix') as base_location_suffix,
  json_extract_scalar(payload, '$.assoc_location_suffix') as assoc_location_suffix,
  json_extract_scalar(payload, '$.diagram_type') as diagram_type,
  json_extract_scalar(payload, '$.CIF_stp_indicator') as stp_indicator
from raw
where rn = 1
