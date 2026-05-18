{#
    This macro returns the description of the payment_type 
#}

{% macro get_train_status(train_status) -%}

    case {{ dbt.safe_cast("train_status", api.Column.translate_type("string")) }}  
        when 'B' then 'Bus (Permanent)'
        when 'F' then 'Freight (Permanent - WTT)'
        when 'P'  then 'Passenger & Parcels (Permanent - WTT)'
        when 'S' then 'Ship (Permanent)'
        when 'T' then 'Trip (Permanent)'
        when '1' then 'STP Passenger & Parcels'
        when '2' then 'STP Freight'
        when '3' then 'STP Trip'
        when '4' then 'STP Ship'
        when '5' then 'STP Bus'
        else null
    end

{%- endmacro %}