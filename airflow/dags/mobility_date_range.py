# pyright: reportMissingImports=false

from datetime import timedelta

from airflow.providers.standard.operators.bash import BashOperator
from airflow.sdk import DAG, Param

DATE_ENV = {
    "START_DATE": "{{ params.start_date }}",
    "END_DATE": "{{ params.end_date }}",
}
DATE_PARAM_SCHEMA = {
    "type": "string",
    "format": "date",
    "pattern": r"^\d{4}-\d{2}-\d{2}$",
}
PROJECT_DIRECTORY = "/opt/airflow/project"

with DAG(
    dag_id="mobility_date_range",
    description="Load a mobility date range and rebuild dbt models",
    schedule=None,
    catchup=False,
    max_active_runs=1,
    max_active_tasks=3,
    dagrun_timeout=timedelta(hours=12),
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
    tags=["mobility", "date-range"],
) as dag:
    validate_dates = BashOperator(
        task_id="validate_dates",
        bash_command=(
            '"$PROJECT_VENV/bin/python" -m orchestration.cli '
            "validate-range "
            '--start-date "$START_DATE" --end-date "$END_DATE"'
        ),
        env=DATE_ENV,
        append_env=True,
        cwd=PROJECT_DIRECTORY,
        retries=0,
        execution_timeout=timedelta(minutes=5),
        do_xcom_push=False,
    )

    weather = BashOperator(
        task_id="weather_pipeline",
        bash_command=(
            '"$PROJECT_VENV/bin/weather-pipeline" pipeline '
            '--start-date "$START_DATE" --end-date "$END_DATE"'
        ),
        env=DATE_ENV,
        append_env=True,
        cwd=PROJECT_DIRECTORY,
        retries=2,
        retry_delay=timedelta(minutes=5),
        execution_timeout=timedelta(hours=2),
        do_xcom_push=False,
    )

    active_mobility = BashOperator(
        task_id="active_mobility_pipeline",
        bash_command=(
            '"$PROJECT_VENV/bin/active-mobility-pipeline" pipeline '
            '--start-date "$START_DATE" --end-date "$END_DATE"'
        ),
        env=DATE_ENV,
        append_env=True,
        cwd=PROJECT_DIRECTORY,
        retries=2,
        retry_delay=timedelta(minutes=5),
        execution_timeout=timedelta(hours=6),
        do_xcom_push=False,
    )

    subway = BashOperator(
        task_id="subway_pipeline",
        bash_command=(
            '"$PROJECT_VENV/bin/mta-subway-pipeline" pipeline '
            '--start-date "$START_DATE" --end-date "$END_DATE"'
        ),
        env=DATE_ENV,
        append_env=True,
        cwd=PROJECT_DIRECTORY,
        retries=2,
        retry_delay=timedelta(minutes=5),
        execution_timeout=timedelta(hours=6),
        do_xcom_push=False,
    )

    dbt_build = BashOperator(
        task_id="dbt_build",
        bash_command=(
            '"$PROJECT_VENV/bin/dbt" build '
            '--project-dir "$DBT_PROFILES_DIR" '
            '--profiles-dir "$DBT_PROFILES_DIR"'
        ),
        append_env=True,
        cwd=PROJECT_DIRECTORY,
        retries=1,
        retry_delay=timedelta(minutes=2),
        execution_timeout=timedelta(hours=1),
        do_xcom_push=False,
    )

    pipeline_tasks = [weather, active_mobility, subway]
    validate_dates >> pipeline_tasks >> dbt_build
