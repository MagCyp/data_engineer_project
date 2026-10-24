# Mobility Analytics dbt Project

This directory contains the dbt transformation layer for the
[NYC Mobility Data Platform](../README.md).

- `models/staging`: typed, explicitly selected views over the `landing` schema.
- `models/intermediate`: hourly active mobility and subway aggregations.
- `models/marts/mobility/facts`: hourly fact tables.
- `models/marts/mobility/dimensions`: date, sensor, and station dimensions.
- `models/marts/mobility/analytics`: daily mobility and weather marts.
- `tests`: singular grain and relationship checks.
- `macros`: shared numeric and timezone transformations.

From the project container:

```bash
dbt build \
  --project-dir /opt/airflow/project/data_platform_analytics \
  --profiles-dir /opt/airflow/project/data_platform_analytics
```

The Airflow mobility DAGs run this build automatically after every successful
set of ingestion tasks.
