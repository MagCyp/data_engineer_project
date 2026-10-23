# pyright: reportMissingImports=false

from datetime import timedelta

from _mobility_dag import RESOLVED_DATE_ENV, create_mobility_dag
from airflow.sdk import Param

YEAR_ENV = {
    "START_YEAR": "{{ params.start_year }}",
    "END_YEAR": "{{ params.end_year }}",
}
YEAR_PARAM_SCHEMA = {
    "type": "string",
    "pattern": r"^\d{4}$",
}

dag = create_mobility_dag(
    dag_id="mobility_year_range",
    description="Load one or more complete mobility years",
    params={
        "start_year": Param(
            title="Start year",
            description="First year to load (YYYY)",
            **YEAR_PARAM_SCHEMA,
        ),
        "end_year": Param(
            title="End year",
            description="Last year to load; use the start year for one year",
            **YEAR_PARAM_SCHEMA,
        ),
    },
    validation_command=(
        '"$PROJECT_VENV/bin/python" -m orchestration.cli '
        "validate-year-range "
        '--start-year "$START_YEAR" --end-year "$END_YEAR"'
    ),
    validation_env=YEAR_ENV,
    pipeline_env=RESOLVED_DATE_ENV,
    tags=["mobility", "year-range"],
    validation_provides_dates=True,
    dagrun_timeout=timedelta(hours=72),
    pipeline_timeout=timedelta(hours=48),
)
