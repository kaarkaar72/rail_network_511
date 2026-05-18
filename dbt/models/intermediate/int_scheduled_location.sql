{{ config(materialized='view', alias='int_scheduled_location') }}

WITH latest_partition AS (
  SELECT MAX(DATE(ingest_ts)) AS latest_date
  FROM {{ ref("stg_rail_schedule") }}
),
stg as (
    select *
    from {{ ref('stg_rail_schedule') }}
    where stp_indicator != 'C'  
    and applicable_timetable is not NULL 
    and schedule_location_json is not NULL
    and DATE(ingest_ts) = (SELECT latest_date FROM latest_partition)
), parsed_locs as(
    select
        train_uid,
        schedule_start_date,
        schedule_end_date,
        stp_indicator,
        loc_offset,
        json_extract_scalar(loc, '$.record_identity') as location_type,
        json_extract_scalar(loc, '$.tiploc_code') as tiploc_code,
        json_extract_scalar(loc, '$.tiploc_instance') as tiploc_instance,
        json_extract_scalar(loc, '$.arrival') as arrival,
        json_extract_scalar(loc, '$.departure') as departure,
        json_extract_scalar(loc, '$.public_arrival') as public_arrival,
        json_extract_scalar(loc, '$.public_departure') as public_departure,
        json_extract_scalar(loc, '$.pass') as pass,
        json_extract_scalar(loc, '$.platform')as platform,
        json_extract_scalar(loc, '$.line') as line,
        json_extract_scalar(loc, '$.path')as path,
        json_extract_scalar(loc, '$.engineering_allowance') as engineering_allowance,
        json_extract_scalar(loc, '$.pathing_allowance') as pathing_allowance,
        json_extract_scalar(loc, '$.performance_allowance') as performance_allowance,
        ingest_ts
    from stg,
    unnest(json_extract_array(schedule_location_json)) as loc with offset as loc_offset
)


select
    train_uid,
    schedule_start_date,
    schedule_end_date,
    stp_indicator,
    location_type,
    {{ parse_location_type('location_type') }} as location_type_desc,
    loc_offset,
    tiploc_code,
    {{ dbt.safe_cast("tiploc_instance", api.Column.translate_type("integer")) }} as tiploc_instance,
    {{ parse_timestamp_sch_loc('arrival') }} as arrival_working_timetable_time,
    {{ parse_timestamp_sch_loc('departure') }} as departure_working_timetable_time,
    {{ parse_timestamp_sch_loc('public_arrival') }} as arrival_public_timetable_time,
    {{ parse_timestamp_sch_loc('public_departure') }} as departure_public_timetable_time,
    {{ parse_timestamp_sch_loc('pass') }} as passing_working_timetable_time,
    
    {{ dbt.safe_cast("platform", api.Column.translate_type("string")) }} as platform,
    {{ dbt.safe_cast("line", api.Column.translate_type("string")) }} as line,
    {{ dbt.safe_cast("path", api.Column.translate_type("string")) }} as path,

    {{ parse_allowance_sch_loc('engineering_allowance') }} as engineering_allowance_mins,
    {{ parse_allowance_sch_loc('pathing_allowance') }} as pathing_allowance_mins,
    {{ parse_allowance_sch_loc('performance_allowance') }} as performance_allowance_mins
from parsed_locs
