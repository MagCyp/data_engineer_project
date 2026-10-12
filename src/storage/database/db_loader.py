from uuid import uuid4

import polars as pl
from psycopg import sql
from sqlalchemy import Column, Connection, MetaData, Table, select
from sqlalchemy.dialects.postgresql import insert

POSTGRES_IDENTIFIER_MAX_LENGTH = 63


def _validate_dataframe_columns(
    dataframe: pl.DataFrame,
    target_table: Table,
) -> list[str]:
    target_columns = list(target_table.columns.keys())
    dataframe_columns = set(dataframe.columns)
    expected_columns = set(target_columns)

    missing_columns = expected_columns - dataframe_columns
    extra_columns = dataframe_columns - expected_columns
    if missing_columns or extra_columns:
        details = []
        if missing_columns:
            details.append(f"missing: {', '.join(sorted(missing_columns))}")
        if extra_columns:
            details.append(f"unexpected: {', '.join(sorted(extra_columns))}")
        raise ValueError(f"DataFrame columns do not match table ({'; '.join(details)})")

    return target_columns


def _stage_table_name(target_table: Table) -> str:
    suffix = uuid4().hex
    prefix_length = POSTGRES_IDENTIFIER_MAX_LENGTH - len(suffix) - 1
    prefix = f"stage_{target_table.name}"[:prefix_length]
    return f"{prefix}_{suffix}"


def _copy_dataframe_into_table(
    data: pl.DataFrame,
    db_connection: Connection,
    stage_table: Table,
    column_names: list[str],
) -> None:
    copy_statement = sql.SQL("COPY {} ({}) FROM STDIN").format(
        sql.Identifier(stage_table.name),
        sql.SQL(", ").join(map(sql.Identifier, column_names)),
    )
    driver_connection = db_connection.connection.driver_connection

    if not driver_connection:
        raise RuntimeError(
            "The database connection does not support the COPY operation. "
            "Ensure that you are using a psycopg connection."
        )

    with driver_connection.cursor() as cursor:
        with cursor.copy(copy_statement) as copy:
            for row in data.select(column_names).iter_rows():
                copy.write_row(row)


def save_into_stage(
    data: pl.DataFrame,
    db_connection: Connection,
    target_table: Table,
) -> Table:
    """Create a transaction-scoped temporary table and load a DataFrame into it."""
    column_names = _validate_dataframe_columns(data, target_table)
    stage_table = Table(
        _stage_table_name(target_table),
        MetaData(),
        *(
            Column(
                column.name,
                column.type,
                nullable=column.nullable,
            )
            for column in target_table.columns
        ),
        prefixes=["TEMPORARY"],
        postgresql_on_commit="DROP",
    )
    stage_table.create(db_connection)

    if not data.is_empty():
        _copy_dataframe_into_table(
            data,
            db_connection,
            stage_table,
            column_names,
        )

    return stage_table


def copy_into_database(
    db_connection: Connection,
    stage_table: Table,
    target_table: Table,
) -> int:
    """Upsert all staged rows into a PostgreSQL target table."""
    column_names = list(target_table.columns.keys())
    missing_columns = set(column_names) - set(stage_table.columns.keys())
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Stage table is missing target columns: {missing}")

    source_rows = select(*(stage_table.c[name] for name in column_names))
    statement = insert(target_table).from_select(column_names, source_rows)

    primary_key_columns = list(target_table.primary_key.columns)
    if primary_key_columns:
        primary_key_names = {column.name for column in primary_key_columns}
        update_values = {
            name: statement.excluded[name]
            for name in column_names
            if name not in primary_key_names
        }
        if update_values:
            statement = statement.on_conflict_do_update(
                index_elements=primary_key_columns,
                set_=update_values,
            )
        else:
            statement = statement.on_conflict_do_nothing(
                index_elements=primary_key_columns,
            )

    result = db_connection.execute(statement.execution_options(preserve_rowcount=True))
    return result.rowcount


def upsert_dataframe(
    data: pl.DataFrame,
    db_connection: Connection,
    target_table: Table,
) -> int:
    """Stage and upsert a DataFrame using the connection's current transaction."""
    stage_table = save_into_stage(data, db_connection, target_table)
    return copy_into_database(db_connection, stage_table, target_table)
