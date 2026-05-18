{#
    This macro returns the description of the payment_type 
#}

{% macro parse_schedule_days_run(col) -%}
    substr({{col}}, 1, 1) = '1' as mon_service,
    substr({{col}}, 2, 1) = '1' as tue_service,
    substr({{col}}, 3, 1) = '1' as wednes_service,
    substr({{col}}, 4, 1) = '1' as thrus_service,
    substr({{col}}, 5, 1) = '1' as fri_service,
    substr({{col}}, 6, 1) = '1' as sat_service,
    substr({{col}}, 7, 1) = '1' as sun_service
{%- endmacro %}