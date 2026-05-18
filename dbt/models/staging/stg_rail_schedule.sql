{{
    config(
        alias = 'stg_rail_schedule',
        materialized = 'incremental',
        unique_key= 'schedule_id',
        incremental_strategy = "insert_overwrite",
        partition_by = {
            "field": "ingest_ts",
            "data_type": "timestamp",
            "granularity": "day"
        },
        cluster_by=['train_uid','schedule_start_date','schedule_end_date']
    )
}}

with raw as (
    select *,
    row_number() over
    (partition by 
      json_extract_scalar(payload, '$.CIF_train_uid'),
      json_extract_scalar(payload,'$.schedule_start_date'),
      json_extract_scalar(payload,'$.schedule_end_date'),
      json_extract_scalar(payload, '$.CIF_stp_indicator')
    order by    
      ingest_ts DESC) as rn
    from {{ source('staging', 'rail_schedule_raw') }}
    where record_type = 'JsonScheduleV1'    
    {% if is_incremental() %}
        -- only scan today’s partition when running incrementally
        and date(ingest_ts) = current_date()
    {% endif %}
)

select
    {{ dbt_utils.generate_surrogate_key([
        "json_extract_scalar(payload, '$.CIF_train_uid')",
        "json_extract_scalar(payload, '$.schedule_start_date')",
        "json_extract_scalar(payload, '$.schedule_end_date')",
        "json_extract_scalar(payload, '$.CIF_stp_indicator')",
        'ingest_ts'
    ]) }} as schedule_id,
    ingest_ts,
    json_extract_scalar(payload, '$.CIF_train_uid') as train_uid,
    json_extract_scalar(payload, '$.transaction_type') as transaction_type,
    cast(json_extract_scalar(payload, '$.schedule_start_date') as date) as schedule_start_date,
    cast(json_extract_scalar(payload, '$.schedule_end_date') as date) as schedule_end_date,
    json_extract_scalar(payload, '$.schedule_days_runs') as schedule_days_runs,
    json_extract_scalar(payload, '$.CIF_bank_holiday_running') as bank_holiday_code,
    json_extract_scalar(payload, '$.train_status') as train_status,
    json_extract_scalar(payload, '$.CIF_stp_indicator') as stp_indicator,
    json_extract_scalar(payload, '$.atoc_code') as atoc_code,
    json_extract_scalar(payload, '$.applicable_timetable') as applicable_timetable,
    json_extract(payload, '$.schedule_segment') as schedule_segment_json,
    json_extract(payload, '$.schedule_segment.schedule_location') as schedule_location_json
from raw
where rn = 1
