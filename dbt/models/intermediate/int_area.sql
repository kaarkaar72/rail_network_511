{{ config(
    materialized='view', 
    alias='int_area'
    ) 
}}

select 
    stanox as station_id,
    upper(nullif(trim(tiploc_code),'')) as tiploc_code,
    nalco as nlc_code,
    upper(nullif(trim(crs_code),'')) as crs_code,
    upper(nullif(trim(description),'')) as location_name
from {{ ref('stg_rail_schedule_tiploc') }}