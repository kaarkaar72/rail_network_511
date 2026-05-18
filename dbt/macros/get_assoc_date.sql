{#
    This macro returns the description of the payment_type 
#}

{% macro get_assoc_date(date_indicator) -%}

    case {{ dbt.safe_cast("date_indicator", api.Column.translate_type("string")) }}  
        when 'S' then 'Standard - the association occurs on the same day'
        when 'N' then 'Over next-midnight - the association occurs the next day'
        when 'P' then 'Over previous-midnight - the association occurs the previous day'
        else null
    end
{%- endmacro %}