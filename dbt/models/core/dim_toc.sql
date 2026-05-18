{{ config(materialized='table') }}

WITH raw as(
    SELECT *
    FROM {{ ref('int_toc') }}
)

SELECT * 
FROM (
    SELECT
        {{ dbt_utils.generate_surrogate_key([
            'toc_name'
        ]) 
        }} as toc_id,
        toc_name,
        business_code as toc_business_code,
        CASE 
            WHEN sector_code = '?' THEN 100
            ELSE cast(sector_code as integer)
        END as toc_operating_code,
        atoc_code as toc_schedule_code,
        current_timestamp() as dbt_updated_at,
        true as is_active
    from raw
    UNION ALL
    SELECT
        {{ dbt_utils.generate_surrogate_key([
        "'Unknown'"
        ]) }} as toc_id,
        "Unknown TOC Name" as toc_name,
        "Unknown Business Code" as toc_business_code,
        null as toc_operating_code,
        "ZZ" as toc_schedule_code,
        current_timestamp() as dbt_updated_at,
        false as is_active
)




