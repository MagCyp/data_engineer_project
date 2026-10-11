from sqlalchemy import MetaData

from storage.database.metadata import LANDING_SCHEMA, metadata


def test_landing_metadata_uses_landing_schema() -> None:
    assert isinstance(metadata, MetaData)
    assert LANDING_SCHEMA == "landing"
    assert metadata.schema == LANDING_SCHEMA
