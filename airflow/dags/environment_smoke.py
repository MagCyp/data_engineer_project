# pyright: reportMissingImports=false

from airflow.providers.standard.operators.bash import BashOperator
from airflow.sdk import DAG

with DAG(
    dag_id="environment_smoke",
    schedule=None,
    catchup=False,
    tags=["smoke"],
) as dag:
    BashOperator(
        task_id="check_weather_pipeline_cli",
        bash_command="weather-pipeline --help",
    )
