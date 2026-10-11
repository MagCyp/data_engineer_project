from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    Float,
    Integer,
    PrimaryKeyConstraint,
    String,
    Table,
)

from storage.database.metadata import metadata

weather_observations = Table(
    "weather_observations",
    metadata,
    Column("location", String(255), nullable=False),
    Column("timezone", String(64), nullable=False),
    Column("observed_at_utc", DateTime(timezone=True), nullable=False),
    Column("temperature_c", Float, nullable=False),
    Column("relative_humidity_pct", Integer, nullable=False),
    Column("precipitation_mm", Float, nullable=False),
    Column("rain_mm", Float, nullable=False),
    Column("wind_speed_kmh", Float, nullable=False),
    Column("ingested_at", DateTime(timezone=True), nullable=False),
    PrimaryKeyConstraint(
        "location",
        "observed_at_utc",
        name="pk_weather_observations",
    ),
    CheckConstraint(
        "relative_humidity_pct BETWEEN 0 AND 100",
        name="ck_weather_observations_humidity",
    ),
    CheckConstraint(
        "precipitation_mm >= 0",
        name="ck_weather_observations_precipitation",
    ),
    CheckConstraint(
        "rain_mm >= 0",
        name="ck_weather_observations_rain",
    ),
    CheckConstraint(
        "wind_speed_kmh >= 0",
        name="ck_weather_observations_wind_speed",
    ),
)
