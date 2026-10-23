# pyright: reportMissingImports=false

from _mobility_dag import create_mobility_dag
from airflow.sdk import Param

DATE_ENV = {
    "START_DATE": "{{ params.start_date }}",
    "END_DATE": "{{ params.end_date }}",
}
DATE_PARAM_SCHEMA = {
    "type": "string",
    "format": "date",
    "pattern": r"^\d{4}-\d{2}-\d{2}$",
}

dag = create_mobility_dag(
    dag_id="mobility_date_range",
    description="Load a mobility date range and rebuild dbt models",
    params={
        "start_date": Param(
            title="Start date",
            description="First day to load, inclusive",
            **DATE_PARAM_SCHEMA,
        ),
        "end_date": Param(
            title="End date",
            description="Last day to load, inclusive",
            **DATE_PARAM_SCHEMA,
        ),
    },
    validation_command=(
        '"$PROJECT_VENV/bin/python" -m orchestration.cli validate-range '
        '--start-date "$START_DATE" --end-date "$END_DATE"'
    ),
    validation_env=DATE_ENV,
    pipeline_env=DATE_ENV,
    tags=["mobility", "date-range"],
)
