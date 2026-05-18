
{{ config(materialized='view', alias='int_toc') }}
with toc as (
  SELECT
    company as toc_name,
    NULLIF(TRIM(business_code), '') AS business_code,
    NULLIF(TRIM(sector_code), '') AS sector_code,
    NULLIF(TRIM(atoc_code), '') AS atoc_code
  FROM
    {{ ref('toc') }}
),toc3 as (
  select 
    *,
    CASE atoc_code 
      WHEN 'ZZ'THEN 'Non-passenger / Freight Operator Type'
      ELSE 'Passenger Operator Type'
    END AS toc_operator_type
  FROM toc
),toc4 as (

  select
      case
          when atoc_code = 'ZZ' and toc_name is not null
              then concat('ZZ_', regexp_replace(lower(toc_name), '[^a-z0-9]+', '_'))
          else atoc_code
      end as cleaned_atoc_code,
      *
  from toc3

)

select 
    toc_name,
    toc_operator_type,
    business_code,
    sector_code,
    cleaned_atoc_code as atoc_code 
from toc4

