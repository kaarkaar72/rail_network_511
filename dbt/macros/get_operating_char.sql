{#
    This macro returns the description of the payment_type 
#}

{% macro get_operating_char(operating_characteristic) -%}

    case {{ dbt.safe_cast("operating_characteristic", api.Column.translate_type("string")) }}  
        when 'B' then 'Vacuum Braked'
        when 'C' then 'Timed at 100 m.p.h.'
        when 'D'  then 'DOO (Coaching stock trains)'
        when 'E' then 'Conveys Mark 4 Coaches'
        when 'G' then 'Trainman (Guard) required'
        when 'M' then 'Timed at 110 m.p.h.'
        when 'P' then 'Push/Pull train'
        when 'Q' then 'Runs as required'
        when 'R' then 'Air conditioned with PA system'
        when 'S' then 'Steam Heated'
        when 'Y' then 'Runs to Terminals/Yards as required'
        when 'Z' then 'May convey traffic to SB1C gauge. Not to be diverted from booked route without authority.'
        else 'UNKNOWN'
    end

{%- endmacro %}