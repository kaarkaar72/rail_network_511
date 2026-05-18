{#
    This macro returns the description of the payment_type 
#}

{% macro get_stp(stp) -%}

    case {{ dbt.safe_cast("stp_indicator", api.Column.translate_type("string")) }}  
        when 'C' then 'STP cancellation of permanent schedule'
        when 'N' then 'New STP schedule (not an overlay)'
        when 'O' then 'STP overlay of permanent schedule'
        when 'P' then 'Permanent'
        else null
    end
{%- endmacro %}
   
