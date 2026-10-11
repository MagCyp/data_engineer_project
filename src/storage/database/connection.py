import os

from dotenv import load_dotenv
from sqlalchemy import URL, Engine, create_engine

DATABASE_ENVIRONMENT_VARIABLES = (
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
    "POSTGRES_HOST",
    "POSTGRES_PORT",
    "POSTGRES_DB",
)


def get_database_url() -> str:
    """Build a SQLAlchemy PostgreSQL URL from environment variables."""
    load_dotenv()

    values = {
        variable: os.getenv(variable) for variable in DATABASE_ENVIRONMENT_VARIABLES
    }
    missing_variables = [variable for variable, value in values.items() if not value]
    if missing_variables:
        missing = ", ".join(missing_variables)
        raise ValueError(f"Missing database environment variables: {missing}")

    try:
        port_value = values["POSTGRES_PORT"]
        if port_value is None:
            raise ValueError("Missing database environment variable: POSTGRES_PORT")
        port = int(port_value)
    except ValueError as error:
        raise ValueError("POSTGRES_PORT must be an integer") from error

    url = URL.create(
        drivername="postgresql+psycopg",
        username=values["POSTGRES_USER"],
        password=values["POSTGRES_PASSWORD"],
        host=values["POSTGRES_HOST"],
        port=port,
        database=values["POSTGRES_DB"],
    )
    return url.render_as_string(hide_password=False)


def get_engine() -> Engine:
    """Create a SQLAlchemy engine without opening a database connection."""
    return create_engine(get_database_url())
