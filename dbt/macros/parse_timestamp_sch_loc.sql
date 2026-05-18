{#
    This macro returns the description of the payment_type 
#}

{% macro parse_timestamp_sch_loc(col) -%}
    SAFE.PARSE_TIME('%H%M', NULLIF(SUBSTR({{ col }}, 1, 4), ''))
{%- endmacro %}
