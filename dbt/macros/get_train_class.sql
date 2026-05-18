{#
    This macro returns the description of the payment_type 
#}

{% macro get_train_class(train_status) -%}

    case {{ dbt.safe_cast("train_class", api.Column.translate_type("string")) }}  
        when 'B' then 'First and Standard'
        when 'S' then 'Standard Only'
        else null
    end

{%- endmacro %}