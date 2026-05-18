{#
    This macro returns the description of the payment_type 
#}

{% macro get_bank_holiday(bank_holiday_code) -%} 
    CASE {{ dbt.safe_cast("bank_holiday_code", api.Column.translate_type("string")) }}
        WHEN 'X' then 'Does not run on specified Bank Holiday Mondays'
        WHEN 'G' then 'Does not run on Glasgow Bank Holidays'
        ELSE null
    END
{%- endmacro %}