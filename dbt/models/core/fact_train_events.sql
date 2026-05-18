{{ config(
    materialized='table',
    alias='fact_train_event'
) }}

with stg as (
    select *
    from {{ ref('stg_rail_describer') }}
    where msg_type != 'CT'
)

SELECT
    {{ dbt_utils.generate_surrogate_key([
        'td_area_id','signal_berth_id','bridge_id','event_ts'
    ]
    )}} as event_id,
    td_area_id,
    COALESCE(signal_berth_id,{{ dbt_utils.generate_surrogate_key(["'Unknown'"]) }}) as signal_berth_id,
    COALESCE(bridge_id,{{ dbt_utils.generate_surrogate_key(["'Unknown'"]) }}) as bridge_id,
    bts.schedule_id,
    bts.train_uid,
    stg.train_signalling_id,
    event_ts,
    ingest_ts,
    msg_type,
    report_time,
FROM
  stg
LEFT JOIN {{ ref('dim_area') }} da ON stg.area_id = da.area_id
LEFT JOIN {{ ref('dim_signal_berth') }} dsb on stg.area_id = dsb.area_id and stg.from_berth = dsb.from_berth and stg.to_berth = dsb.to_berth
LEFT JOIN {{ ref('bridge_td_to_schedule')}} bts on stg.train_signalling_id = bts.train_signalling_id and (DATE(stg.event_ts) between bts.schedule_start_date and bts.schedule_end_date)
WHERE bts.train_uid is not null