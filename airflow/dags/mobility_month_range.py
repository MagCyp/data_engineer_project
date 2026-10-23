# pyright: reportMissingImports=false

from _mobility_dag import RESOLVED_DATE_ENV, create_mobility_dag
from airflow.sdk import Param

MONTH_ENV = {
    "START_MONTH": "{{ params.start_month }}",
    "END_MONTH": "{{ params.end_month }}",
}
MONTH_PARAM_SCHEMA = {
    "type": "string",
    "pattern": r"^\d{4}-(0[1-9]|1[0-2])$",
}

dag = create_mobility_dag(
    dag_id="mobility_month_range",
    description="Load one or more complete mobility months",
    params={
        "start_month": Param(
            title="Start month",
            description="First month to load (YYYY-MM)",
            **MONTH_PARAM_SCHEMA,
        ),
        "end_month": Param(
            title="End month",
            description=(
                "Last month to load; use the start month for one month"
            ),
            **MONTH_PARAM_SCHEMA,
        ),
    },
    validation_command=(
        '"$PROJECT_VENV/bin/python" -m orchestration.cli '
        "validate-month-range "
        '--start-month "$START_MONTH" --end-month "$END_MONTH"'
    ),
    validation_env=MONTH_ENV,
    pipeline_env=RESOLVED_DATE_ENV,
    tags=["mobility", "month-range"],
    validation_provides_dates=True,
)
