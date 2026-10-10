from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml

project_root = Path(__file__).resolve().parents[2]
file_path = project_root / "config" / "project.yml"


def load_config() -> dict[str, Any]:
    with open(file_path, "r") as file:
        config = yaml.safe_load(file)
    return config


def get_storage_path(
    config: Mapping[str, Any],
    *,
    storage_key: str,
    year: int,
    month: int,
) -> Path:
    """Resolve a year/month-partitioned storage path from the config."""
    if year < 1:
        raise ValueError("year must be greater than 0")
    if not 1 <= month <= 12:
        raise ValueError("month must be between 1 and 12")

    path_template = str(config["storage"][storage_key])
    path = Path(
        path_template.format(
            year=year,
            month=f"{month:02d}",
        )
    )

    if path.is_absolute():
        return path

    return project_root / path
