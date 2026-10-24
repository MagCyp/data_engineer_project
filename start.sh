#!/usr/bin/env sh
set -eu

project_root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$project_root"

export AIRFLOW_UID="${AIRFLOW_UID:-$(id -u)}"

mkdir -p \
    data \
    airflow/logs \
    airflow/config \
    airflow/plugins \
    data_platform_analytics/logs \
    data_platform_analytics/target

docker compose up --build --wait "$@"

printf '%s\n' "Data platform is ready: http://localhost:8080"
