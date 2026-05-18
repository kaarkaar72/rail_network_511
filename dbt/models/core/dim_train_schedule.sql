{{
  config(
    materialized='table',
    alias='dim_train_schedule'
  )
}}

with header as (
    select *
    from {{ ref('int_scheduled_header') }}
)

select
  {{ dbt_utils.generate_surrogate_key([
      'train_uid',
      'train_signalling_id',
      'train_service_code',
      'schedule_start_date',
      'schedule_end_date',
      'stp_indicator'
      ]) }} as schedule_id,
  train_uid,
  train_signalling_id,
  train_service_code,
  atoc_code,
  stp_indicator,
  stp_indicator_desc as short_term_planning_schedule_indicator,
  schedule_start_date,
  schedule_end_date, 
  planned_speed,
  tc.Category as train_category,
  tc.Description as train_category_desc,
  train_status_desc, 
  reservations_desc,
  operating_characteristic_desc,
  power_type_desc,
  mon_service,tue_service,wednes_service,thrus_service,fri_service,sat_service,sun_service,
  bank_holiday_desc,
  current_timestamp() as dbt_updated_at
from header 
left join {{ ref('train_category')}} tc on header.train_category = tc.Code