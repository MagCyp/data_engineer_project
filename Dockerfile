FROM apache/airflow:3.3.2-python3.14

ENV PROJECT_HOME=/opt/airflow/project \
    PROJECT_VENV=/opt/airflow/project-venv \
    DBT_PROFILES_DIR=/opt/airflow/project/data_platform_analytics \
    PYTHONPATH=/opt/airflow/project/src

WORKDIR ${PROJECT_HOME}

COPY --chown=airflow:root pyproject.toml ./
COPY --chown=airflow:root src ./src

RUN python -m venv "${PROJECT_VENV}" \
    && "${PROJECT_VENV}/bin/pip" install --no-cache-dir .

ENV PATH="${PROJECT_VENV}/bin:${PATH}"

COPY --chown=airflow:root alembic ./alembic
COPY --chown=airflow:root alembic.ini ./
COPY --chown=airflow:root config ./config
COPY --chown=airflow:root data_platform_analytics ./data_platform_analytics
COPY --chown=airflow:root airflow/dags /opt/airflow/dags
