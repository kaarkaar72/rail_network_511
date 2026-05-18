{#
    This macro returns the description of the payment_type 
#}

{% macro parse_allowance_sch_loc(col) -%}
 CASE
    WHEN LENGTH({{ col }}) = 1 AND SUBSTR({{ col }},1,1) = 'H' THEN 0.5
    WHEN LENGTH({{ col }}) = 1 AND SAFE_CAST(SUBSTR({{ col }},1,1) AS FLOAT64) IS NOT NULL THEN CAST({{ col }} AS INT64)
    WHEN LENGTH({{ col }}) = 2 AND SAFE_CAST(SUBSTR({{ col }},1,1) AS FLOAT64) IS NOT NULL AND SUBSTR({{ col }},2,1) = 'H' THEN CAST(SUBSTR({{ col }},1,1) AS INT64) + 0.5
    WHEN LENGTH({{ col }}) = 2 AND SAFE_CAST(SUBSTR({{ col }},1,1) AS FLOAT64) IS NOT NULL THEN CAST({{ col }} AS INT64)
    ELSE null
END
{%- endmacro %}




