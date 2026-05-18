{{
  config(
    materialized='table',
    alias='dim_train_association'
  )
}}

with header as (
    select 
      association_id,main_train_uid,assoc_train_uid,
      assoc_start_date,assoc_end_date,
      {{ get_assoc_type('assoc_category') }} as associated_type,
      {{ get_assoc_date('date_indicator') }} as associated_date_indicator,
      {{ parse_schedule_days_run('assoc_days') }},
      assoc_location,base_location_suffix,assoc_location_suffix
    from {{ ref('stg_rail_schedule_association') }}
)

select
  *
from header