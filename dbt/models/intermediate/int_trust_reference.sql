{{ config(
    materialized='view', 
    alias='int_trust_reference') }}
SELECT 
    stanox as station_id,
    UPPER(NULLIF(TRIM(tiploc), '')) AS tiploc_code,
    nlc as nlc_code,
    UPPER(NULLIF(TRIM(three_alpha), '')) AS crs_code,
    UPPER(NULLIF(TRIM(nlc_desc), '')) AS location_name
FROM {{ ref('trust_corpus') }} 
