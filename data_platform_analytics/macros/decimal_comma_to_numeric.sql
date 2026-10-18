{% macro decimal_comma_to_numeric(column_name, precision=9, scale=6) -%}
    cast(replace(nullif(trim({{ column_name }}), ''), ',', '.') as numeric({{ precision }}, {{ scale }}))
{%- endmacro %}
