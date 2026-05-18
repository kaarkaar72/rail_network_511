{#
    This macro returns the description of the payment_type 
#}

{% macro get_reservations(reservations) -%}

    case {{ dbt.safe_cast("reservations", api.Column.translate_type("string")) }}  
        when 'A' then 'Reservations compulsory'
        when 'E' then 'Reservations for bicycles essential'
        when 'R' then 'Reservations recommended'
        when 'S' then 'Reservations possible from any station'
        else null
    end

{%- endmacro %}
