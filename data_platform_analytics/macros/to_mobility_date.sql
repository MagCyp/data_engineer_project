{% macro to_mobility_date(timestamp_expression) -%}
    cast(
        {{ timestamp_expression }} at time zone '{{ var("mobility_timezone") }}'
        as date
    )
{%- endmacro %}
