{{ config(
        alias='stg_rail_movement',
        materialized='incremental',
        unique_key = 'movement_id',  
        incremental_strategy = 'merge',
        partition_by = {
            "field": "ingest_ts",
            "data_type": "timestamp",
            "granularity": "day"
        }
    ) 
}}

with movement_raw as (
    select *,
    row_number() over (partition by train_id,loc_stanox,actual_timestamp) as rn
    from {{ source('staging', 'rail_movement_clean') }}
    {% if is_incremental() %}
        -- only scan today’s partition when running incrementally
        where date(ingest_ts) = current_date()
    {% endif %}
)

select
    -- Surrogate key to uniquely identify a record
    {{ dbt_utils.generate_surrogate_key([
        'train_id',
        'toc_id',
        'next_report_stanox',
        'loc_stanox',
        'actual_timestamp'
    ]) }} as movement_id,

    -- Identifiers
    train_id,
    {{ dbt.safe_cast('division_code', api.Column.translate_type('string')) }} as division_code,
    {{ dbt.safe_cast('toc_id', api.Column.translate_type('integer')) }} as toc_id,
    {{ dbt.safe_cast('route', api.Column.translate_type('string')) }} as route,
    {{ dbt.safe_cast('loc_stanox', api.Column.translate_type('integer')) }} as loc_stanox,
    {{ dbt.safe_cast('next_report_stanox', api.Column.translate_type('integer')) }} as next_report_stanox,
    {{ dbt.safe_cast('reporting_stanox', api.Column.translate_type('integer')) }} as reporting_stanox,
    {{ dbt.safe_cast('platform', api.Column.translate_type('string')) }} as platform,
    
    -- Timestamps
    cast(actual_timestamp as timestamp) as actual_timestamp,
    cast(planned_timestamp as timestamp) as planned_timestamp,

    -- Event details
    {{ dbt.safe_cast('planned_event_type', api.Column.translate_type('string')) }} as planned_event_type,
    {{ dbt.safe_cast('event_type', api.Column.translate_type('string')) }} as event_type,
    {{ dbt.safe_cast('timetable_variation', api.Column.translate_type('integer')) }} as timetable_variation,
    {{ dbt.safe_cast('variation_status', api.Column.translate_type('string')) }} as variation_status,
    {{ dbt.safe_cast('next_report_run_time', api.Column.translate_type('integer')) }} as next_report_run_time,
    {{ dbt.safe_cast('correction_ind', api.Column.translate_type('boolean')) }} as correction_ind,
    {{ dbt.safe_cast('offroute_ind', api.Column.translate_type('boolean')) }} as offroute_ind,
    {{ dbt.safe_cast('train_terminated', api.Column.translate_type('boolean')) }} as train_terminated,
    {{ dbt.safe_cast('delay_monitoring_point', api.Column.translate_type('boolean')) }} as delay_monitoring_point,
    {{ dbt.safe_cast('auto_expected', api.Column.translate_type('boolean')) }} as auto_expected,
    {{ dbt.safe_cast('event_source', api.Column.translate_type('string')) }} as event_source,

    -- Metadata
    {{ dbt.safe_cast('msg_type', api.Column.translate_type('string')) }} as msg_type,
    cast(ingest_ts as timestamp) as ingest_ts

from movement_raw
where rn = 1

