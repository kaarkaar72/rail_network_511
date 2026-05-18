{{
    config(
        alias = 'stg_rail_td_describer',
        materialized = 'incremental',
        unique_key= 'describer_id',
        incremental_strategy = "insert_overwrite",
        partition_by = {
            "field": "ingest_ts",
            "data_type": "timestamp",
            "granularity": "day"
        }
    )
}}

with raw as (
    select *,
    row_number() over (partition by 
                area_id,
                event_ts,  
                coalesce(from_berth, ''), 
                coalesce(to_berth, ''), 
                coalesce(descr, '')) as rn
    from {{ source('staging', 'rail_td_mov_clean') }}
    {% if is_incremental() %}
        -- only scan today’s partition when running incrementally
        where date(ingest_ts) = current_date()
    {% endif %}
)

select
    -- Surrogate key
    {{ dbt_utils.generate_surrogate_key([
        "area_id",
        "event_ts",
        "coalesce(from_berth, '')",
        "coalesce(to_berth, '')",
        "coalesce(descr, '')"
    ]) }} as describer_id,

    -- Metadata
    cast(msg_type as string) as msg_type,
    cast(area_id as string) as area_id,
    cast(event_ts as timestamp) as event_ts,
    cast(ingest_ts as timestamp) as ingest_ts,

    -- Movement data
    cast(from_berth as string) as from_berth,
    cast(to_berth as string) as to_berth,
    CASE
      WHEN TRIM(descr) = '' THEN NULL
      ELSE TRIM(descr)
    END as train_signalling_id,
    cast(report_time as string) as report_time  -- optional parsing if needed
from raw
where rn = 1


