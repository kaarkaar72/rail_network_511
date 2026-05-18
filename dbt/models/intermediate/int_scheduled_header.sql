{{
  config(
    materialized='view',
    alias='int_scheduled_header'
  )
}}

WITH latest_partition AS (
  SELECT MAX(DATE(ingest_ts)) AS latest_date
  FROM {{ ref("stg_rail_schedule") }}
),header as (
  select
    ingest_ts,
    train_uid,
    transaction_type,
    schedule_start_date,
    schedule_end_date,
    schedule_days_runs,
    bank_holiday_code,
    train_status,
    stp_indicator,
    atoc_code,
    applicable_timetable,
    schedule_segment_json, 
    schedule_location_json
  from {{ ref("stg_rail_schedule") }}
  WHERE DATE(ingest_ts) = (SELECT latest_date FROM latest_partition)
),
parsed as(
  SELECT
    ingest_ts,
    train_uid,
    stp_indicator,
    atoc_code,
    transaction_type,
    schedule_start_date,
    schedule_end_date, 
    schedule_days_runs,
    bank_holiday_code,
    train_status,
    applicable_timetable,
    json_extract_scalar(schedule_segment_json, '$.signalling_id') as train_signalling_id,
    json_extract_scalar(schedule_segment_json, '$.CIF_train_category') as train_category,
    json_extract_scalar(schedule_segment_json, '$.CIF_headcode') as headcode,
    json_extract_scalar(schedule_segment_json, '$.CIF_train_service_code') as train_service_code,
    json_extract_scalar(schedule_segment_json, '$.CIF_operating_characteristics') as operating_characteristic,
    json_extract_scalar(schedule_segment_json, '$.CIF_power_type') as power_type,
    json_extract_scalar(schedule_segment_json, '$.CIF_speed') as planned_speed,
    json_extract_scalar(schedule_segment_json, '$.CIF_train_class') as train_class,
    json_extract_scalar(schedule_segment_json, '$.CIF_reservations') as reservations,
  from header
  
)

SELECT
    train_uid,
    CASE
      WHEN TRIM(train_signalling_id) = '' THEN NULL
      ELSE TRIM(train_signalling_id)
    END as train_signalling_id,
    CASE
      WHEN TRIM(train_service_code) = '' THEN NULL
      ELSE TRIM(train_service_code)
    END as train_service_code,
    train_category,
    stp_indicator,
    {{ get_stp(stp_indicator) }} as stp_indicator_desc,
    atoc_code,
    schedule_start_date,
    schedule_end_date, 
    schedule_days_runs,
    {{ parse_schedule_days_run('schedule_days_runs') }},
    CAST(planned_speed as integer) as planned_speed,
    train_status,
    {{ get_train_status('train_status') }} as train_status_desc,
    operating_characteristic,
    {{ get_operating_char('operating_characteristic')}} as operating_characteristic_desc,
    power_type,
    {{ get_power_type('power_type')}} as power_type_desc,
    reservations,
    {{ get_reservations('reservations')}} as reservations_desc,
    bank_holiday_code,
    {{ get_bank_holiday('bank_holiday_code')}} as bank_holiday_desc,
    ingest_ts
FROM parsed




