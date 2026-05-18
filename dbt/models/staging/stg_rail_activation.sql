{{ config(
    alias='stg_rail_activation',
    materialized='incremental',
    unique_key = 'activation_id',
    incremental_strategy = 'merge',
        partition_by = {
            "field": "ingest_ts",
            "data_type": "timestamp",
            "granularity": "day"
        }
    )  
}}


with activation_raw as (
    select *,
    row_number() over (partition by train_id,train_uid,schedule_start_date,schedule_type,tp_origin_timestamp,origin_dep_timestamp,creation_timestamp) as rn
    from {{ source('staging', 'rail_activation_clean') }}
    {% if is_incremental() %}
    -- only scan today’s partition when running incrementally
    where date(ingest_ts) = current_date()
    {% endif %}
)
select
    {{ dbt_utils.generate_surrogate_key([
        'train_id',
        'train_uid',
        'schedule_start_date',
        'schedule_type',
        'tp_origin_timestamp',
        'origin_dep_timestamp',
        'creation_timestamp'
    ]) }} as activation_id,
    ingest_ts,
    msg_type,
    train_id,
    train_uid,
    train_service_code,
    train_file_address,
    schedule_type,
    schedule_source,
    cast(schedule_start_date as date) as schedule_start_date,
    cast(schedule_end_date as date) as schedule_end_date,
    schedule_wtt_id,
    sched_origin_stanox,
    tp_origin_stanox,
    cast(tp_origin_timestamp as timestamp) as tp_origin_timestamp,
    cast(origin_dep_timestamp as timestamp) as origin_dep_timestamp,
    cast(creation_timestamp as timestamp) as creation_timestamp,
    train_call_type,
    train_call_mode,
    toc_id,
    d1266_record_number,
    source_dev_id,
    user_id,
    original_data_source,
    source_system_id,
    cast(msg_queue_timestamp as timestamp) as msg_queue_timestamp
from activation_raw
where rn = 1
