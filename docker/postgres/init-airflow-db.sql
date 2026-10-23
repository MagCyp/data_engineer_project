\getenv airflow_db_name AIRFLOW_DB_NAME
\getenv airflow_db_user AIRFLOW_DB_USER
\getenv airflow_db_password AIRFLOW_DB_PASSWORD

select format(
    'create role %I login password %L',
    :'airflow_db_user',
    :'airflow_db_password'
)
where not exists (
    select 1
    from pg_roles
    where rolname = :'airflow_db_user'
)
\gexec

select format(
    'alter role %I with login password %L',
    :'airflow_db_user',
    :'airflow_db_password'
)
\gexec

select format(
    'create database %I owner %I',
    :'airflow_db_name',
    :'airflow_db_user'
)
where not exists (
    select 1
    from pg_database
    where datname = :'airflow_db_name'
)
\gexec

select format(
    'alter database %I owner to %I',
    :'airflow_db_name',
    :'airflow_db_user'
)
\gexec
