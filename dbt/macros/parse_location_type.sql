{#
    This macro returns the description of the payment_type 
#}

{% macro parse_location_type(col) -%}    
    CASE {{ col }}
        WHEN 'LO' THEN ' Originating location - location where the train service starts from'
        WHEN 'LI' THEN 'Intermediate location'
        WHEN 'LT' THEN 'Terminating location - where the service terminates'
        ELSE null
    END
{%- endmacro %}