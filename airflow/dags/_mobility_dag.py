# pyright: reportMissingImports=false

from collections.abc import Mapping, Sequence
from datetime import timedelta

from airflow.providers.standard.operators.bash import BashOperator
from airflow.sdk import DAG

PROJECT_DIRECTORY = "/opt/airflow/project"
RESOLVED_DATE_ENV = {
    "START_DATE": (
        "{{ ti.xcom_pull(task_ids='validate_dates').split()[0] }}"
    ),
    "END_DATE": "{{ ti.xcom_pull(task_ids='validate_dates').split()[1] }}",
}


def create_mobility_dag(
    *,
    dag_id: str,
    description: str,
    params: Mapping[str, object],
    validation_command: str,
    validation_env: Mapping[str, str],
    pipeline_env: Mapping[str, str],
    tags: Sequence[str],
    validation_provides_dates: bool = False,
    dagrun_timeout: timedelta = timedelta(hours=12),
    pipeline_timeout: timedelta = timedelta(hours=6),
) -> DAG:
    dag = DAG(
        dag_id=dag_id,
        description=description,
        schedule=None,
        catchup=False,
        max_active_runs=1,
        max_active_tasks=3,
        dagrun_timeout=dagrun_timeout,
        params=dict(params),
        tags=list(tags),
    )

    with dag:
        validate_dates = BashOperator(
            task_id="validate_dates",
            bash_command=validation_command,
            env=dict(validation_env),
            append_env=True,
            cwd=PROJECT_DIRECTORY,
            retries=0,
            execution_timeout=timedelta(minutes=5),
            do_xcom_push=validation_provides_dates,
        )

        weather = BashOperator(
            task_id="weather_pipeline",
            bash_command=(
                '"$PROJECT_VENV/bin/weather-pipeline" pipeline '
                '--start-date "$START_DATE" --end-date "$END_DATE"'
            ),
            env=dict(pipeline_env),
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
            env=dict(pipeline_env),
            append_env=True,
            cwd=PROJECT_DIRECTORY,
            retries=2,
            retry_delay=timedelta(minutes=5),
            execution_timeout=pipeline_timeout,
            do_xcom_push=False,
        )

        subway = BashOperator(
            task_id="subway_pipeline",
            bash_command=(
                '"$PROJECT_VENV/bin/mta-subway-pipeline" pipeline '
                '--start-date "$START_DATE" --end-date "$END_DATE"'
            ),
            env=dict(pipeline_env),
            append_env=True,
            cwd=PROJECT_DIRECTORY,
            retries=2,
            retry_delay=timedelta(minutes=5),
            execution_timeout=pipeline_timeout,
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

    return dag
