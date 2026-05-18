{#
    This macro returns the description of the payment_type 
#}

{% macro get_assoc_type(assoc_category) -%}

    case {{ dbt.safe_cast("assoc_category", api.Column.translate_type("string")) }}  
        when 'JJ' then 'Join'
        when 'NP' then 'Next'
        when 'VV' then 'Divide'
        else null
    end
{%- endmacro %}