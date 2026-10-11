from unittest.mock import Mock

import pytest

from storage.database import connection

DATABASE_ENVIRONMENT = {
    "POSTGRES_USER": "data_platform_user",
    "POSTGRES_PASSWORD": "p@ss/word",
    "POSTGRES_HOST": "localhost",
    "POSTGRES_PORT": "5433",
    "POSTGRES_DB": "data_platform_dw",
}


def set_database_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    for variable, value in DATABASE_ENVIRONMENT.items():
        monkeypatch.setenv(variable, value)


def test_get_database_url_loads_env_and_builds_psycopg_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    load_dotenv = Mock()
    monkeypatch.setattr(connection, "load_dotenv", load_dotenv)
    set_database_environment(monkeypatch)

    result = connection.get_database_url()

    assert result == (
        "postgresql+psycopg://data_platform_user:"
        "p%40ss%2Fword@localhost:5433/data_platform_dw"
    )
    load_dotenv.assert_called_once_with()


@pytest.mark.parametrize("missing_variable", DATABASE_ENVIRONMENT)
def test_get_database_url_rejects_missing_variables(
    monkeypatch: pytest.MonkeyPatch,
    missing_variable: str,
) -> None:
    monkeypatch.setattr(connection, "load_dotenv", Mock())
    set_database_environment(monkeypatch)
    monkeypatch.delenv(missing_variable)

    with pytest.raises(
        ValueError,
        match=f"Missing database environment variables: {missing_variable}",
    ):
        connection.get_database_url()


def test_get_database_url_rejects_non_numeric_port(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(connection, "load_dotenv", Mock())
    set_database_environment(monkeypatch)
    monkeypatch.setenv("POSTGRES_PORT", "not-a-port")

    with pytest.raises(ValueError, match="POSTGRES_PORT must be an integer"):
        connection.get_database_url()


def test_get_engine_uses_psycopg_driver(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(connection, "load_dotenv", Mock())
    set_database_environment(monkeypatch)

    engine = connection.get_engine()

    assert engine.dialect.name == "postgresql"
    assert engine.dialect.driver == "psycopg"
    assert engine.url.port == 5433
    engine.dispose()
