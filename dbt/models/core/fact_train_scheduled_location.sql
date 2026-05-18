{{
  config(
    materialized='table',
    alias='fact_train_scheduled_location'
  )
}}



with sch_locs as (
    select * 
    from {{ ref('int_scheduled_location') }}
    where stp_indicator != 'C'
),
dim_locs as (
    select location_id,tiploc_code 
    from {{ ref('dim_location') }}

),
dim_sch as (
    select schedule_id,train_uid,stp_indicator,schedule_start_date,schedule_end_date
    from {{ ref('dim_train_schedule')}}
    where stp_indicator != 'C'
)


select 
    {{ dbt_utils.generate_surrogate_key([
        'ds.schedule_id','dl.location_id',
        'sl.loc_offset','sl.location_type_desc',
        'sl.arrival_working_timetable_time', 'sl.departure_working_timetable_time',
        'sl.departure_public_timetable_time','sl.arrival_public_timetable_time',
        'sl.passing_working_timetable_time'
    ]) }} as scheduled_location_id,
    COALESCE(ds.schedule_id,{{ dbt_utils.generate_surrogate_key(["'Unknown'"])}}) as schedule_id,
    COALESCE(dl.location_id, {{ dbt_utils.generate_surrogate_key(["'Unknown'"])}}) as location_id, 
    sl.loc_offset,sl.location_type_desc,
    sl.arrival_working_timetable_time,sl.departure_working_timetable_time,
    sl.arrival_public_timetable_time,sl.departure_public_timetable_time,
    sl.passing_working_timetable_time,
    sl.platform,sl.line,sl.path,
        sl.engineering_allowance_mins,sl.pathing_allowance_mins,sl.performance_allowance_mins
from sch_locs sl
left join dim_sch ds 
    on sl.train_uid = ds.train_uid 
    and sl.schedule_start_date = ds.schedule_start_date
    and sl.schedule_end_date = ds.schedule_end_date
    and sl.stp_indicator = ds.stp_indicator
left join dim_locs dl
    on sl.tiploc_code = dl.tiploc_code

