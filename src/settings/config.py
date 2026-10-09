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
    storage_key: str,
) -> Path:
    """Resolve a configured storage path relative to the project root."""
    path = Path(config["storage"][storage_key])

    if path.is_absolute():
        return path

    return project_root / path
