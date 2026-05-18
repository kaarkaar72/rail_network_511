{#
    This macro returns the description of the payment_type 
#}

{% macro get_power_type(power_type) -%}

    case {{ dbt.safe_cast("power_type", api.Column.translate_type("string")) }}  
        when 'D' then 'Diesel'
        when 'DEM' then 'Diesel Electric Multiple Unit'
        when 'DMU' then 'Diesel Mechanical Multiple Unit'
        when 'E' then 'Electric'
        when 'ED' then 'Electro-Diesel'
        when 'EML' then 'EMU plus D, E, ED locomotive'
        when 'EMU' then 'Electric Multiple Unit'
        when 'HST' then 'High Speed Train'
        else null
    end
{%- endmacro %}