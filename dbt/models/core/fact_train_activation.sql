{{ config(
    materialized='table',
    alias='fact_train_activation'
) }}

with stg as (
    select *
    from {{ ref('stg_rail_activation') }}
)

select
    {{ dbt_utils.generate_surrogate_key([
        'ds.schedule_id','dtoc.toc_id','fa.train_id','fa.schedule_start_date','fa.schedule_end_date'
    ]) }} as activation_id,
    ds.schedule_id,
    dtoc.toc_id,
    fa.train_id,
    fa.train_service_code,
    fa.schedule_wtt_id,
    fa.sched_origin_stanox,
    fa.tp_origin_stanox,
    fa.tp_origin_timestamp,
    fa.origin_dep_timestamp,
    fa.train_call_type,
    fa.train_call_mode,
    fa.user_id,
    fa.original_data_source,
    fa.source_system_id,
    fa.msg_queue_timestamp,
    fa.ingest_ts,
    true as is_active,
    current_timestamp() as dbt_updated_at,
from stg fa
left join {{ ref('dim_train_schedule') }} ds
    on fa.train_uid = ds.train_uid 
    and fa.schedule_start_date = ds.schedule_start_date
    and fa.schedule_end_date = ds.schedule_end_date
    and fa.schedule_type = ds.stp_indicator
left join {{ ref('dim_toc') }} dtoc
    on fa.toc_id = dtoc.toc_operating_code
where fa.train_id is not null
and ds.train_uid is not null