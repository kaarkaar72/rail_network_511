{{ config(
    materialized='incremental',
    unique_key='train_movement_id',
    incremental_strategy='merge',
    alias='fact_train_movement'
) }}

with stg as (
    select ds.schedule_id,fa.train_id,fa.schedule_start_date,fa.schedule_end_date,fa.schedule_type
    from {{ ref('stg_rail_activation') }} fa
    left join {{ ref('dim_train_schedule') }} ds
        on fa.train_uid = ds.train_uid 
        and fa.schedule_start_date = ds.schedule_start_date
        and fa.schedule_end_date = ds.schedule_end_date
        and fa.schedule_type = ds.stp_indicator
    where ds.train_uid is not null
),
-- Join with dimensions to get surrogate keys
joined as (
    select
        {{ dbt_utils.generate_surrogate_key([
        'l.train_id',
        'stg.schedule_id',
        'dl.location_id',
        'nl.location_id',
        'dtoc.toc_id',
        'actual_timestamp'
        ]) }} as train_movement_id,
        l.train_id,
        COALESCE(stg.schedule_id, {{ dbt_utils.generate_surrogate_key(["'Unknown'"]) }}) as schedule_id,--Foreign Key
        COALESCE(dl.location_id, {{ dbt_utils.generate_surrogate_key(["'Unknown'"]) }}) as location_id, -- Foreign Key
        COALESCE(nl.location_id, {{ dbt_utils.generate_surrogate_key(["'Unknown'"]) }}) as next_location_id,
        COALESCE(dtoc.toc_id, {{ dbt_utils.generate_surrogate_key(["'Unknown'"]) }} ) as toc_id,-- Foreign Key

        l.route,
        l.platform,
        l.loc_stanox,
        l.next_report_stanox,
        l.reporting_stanox,
        --Event Details
        l.actual_timestamp,
        l.planned_timestamp,
        l.planned_event_type,
        l.event_type,
        l.timetable_variation,
        l.variation_status,
        l.next_report_run_time,
        l.correction_ind,
        l.offroute_ind,
        l.train_terminated,
        l.delay_monitoring_point,
        l.auto_expected,
        l.event_source,
        l.msg_type,
        l.ingest_ts,
        true as is_active,
        current_timestamp() as dbt_updated_at
    from {{ ref('stg_rail_movement')}} l 
        left join stg
            on l.train_id = stg.train_id
        left join {{ ref('dim_location') }} dl
            on l.loc_stanox = dl.station_id
        left join {{ ref('dim_location')}} nl
            on l.next_report_stanox = nl.station_id
        left join {{ ref('dim_toc') }} dtoc
            on l.toc_id = dtoc.toc_operating_code
    where stg.train_id is not null
    and dtoc.toc_operating_code is not null 

)

select * from joined
