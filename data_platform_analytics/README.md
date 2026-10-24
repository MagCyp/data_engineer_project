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

## Documentation and lineage graph

From the repository root, start the optional dbt Docs service:

```bash
docker compose --profile docs up -d --wait dbt-docs
```

Open [http://localhost:8081](http://localhost:8081) to browse models, columns,
tests, sources, compiled SQL, and the lineage graph. Restart `dbt-docs` after
changing dbt files so that it regenerates `manifest.json` and `catalog.json`.
