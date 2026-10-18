from collections.abc import Mapping
from pathlib import Path
from typing import Any

from settings.config import get_storage_path


def get_partition_file_path(
    config: Mapping[str, Any],
    *,
    pipeline_name: str,
    filename: str,
    year: int,
    month: int,
    storage_key: str,
) -> Path:
    """Return a file inside a configured year/month pipeline partition."""
    return (
        get_storage_path(
            config,
            storage_key=storage_key,
            pipeline_name=pipeline_name,
            year=year,
            month=month,
        )
        / filename
    )
