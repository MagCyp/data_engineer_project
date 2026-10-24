from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml

project_root = Path(__file__).resolve().parents[2]
file_path = project_root / "config" / "project.yml"


def load_config() -> dict[str, Any]:
    with file_path.open(encoding="utf-8") as config_file:
        config = yaml.safe_load(config_file)
    if not isinstance(config, dict):
        raise ValueError("Project configuration must be a mapping")
    return config


def get_api_config(
    config: Mapping[str, Any],
    api_name: str,
) -> Mapping[str, Any]:
    """Return configuration for a named external API."""
    api_config = _get_named_config(
        config,
        section="apis",
        name=api_name,
        label="API",
    )
    http_config = config.get("http")
    if not isinstance(http_config, Mapping):
        raise ValueError("HTTP configuration must be a mapping")
    return {**http_config, **api_config}


def get_pipeline_config(
    config: Mapping[str, Any],
    pipeline_name: str,
) -> Mapping[str, Any]:
    """Return configuration for a named data pipeline."""
    return _get_named_config(
        config,
        section="pipelines",
        name=pipeline_name,
        label="Pipeline",
    )


def _get_named_config(
    config: Mapping[str, Any],
    *,
    section: str,
    name: str,
    label: str,
) -> Mapping[str, Any]:
    configured_items = config.get(section)
    if not isinstance(configured_items, Mapping) or name not in configured_items:
        raise ValueError(f"{label} '{name}' is not configured")

    item_config = configured_items[name]
    if not isinstance(item_config, Mapping):
        raise ValueError(f"{label} '{name}' configuration must be a mapping")
    return item_config


def get_storage_path(
    config: Mapping[str, Any],
    *,
    storage_key: str,
    pipeline_name: str,
    year: int | None = None,
    month: int | None = None,
) -> Path:
    """Resolve a pipeline storage path from its configured template."""
    if year is not None and year < 1:
        raise ValueError("year must be greater than 0")
    if month is not None and not 1 <= month <= 12:
        raise ValueError("month must be between 1 and 12")

    storage_config = config.get("storage")
    if not isinstance(storage_config, Mapping) or storage_key not in storage_config:
        raise ValueError(f"Storage path '{storage_key}' is not configured")

    path_template = storage_config[storage_key]
    if not isinstance(path_template, str) or not path_template.strip():
        raise ValueError(f"Storage path '{storage_key}' must be a non-empty string")
    template_values: dict[str, str | int] = {
        "pipeline_name": pipeline_name,
    }
    if year is not None:
        template_values["year"] = year
    if month is not None:
        template_values["month"] = f"{month:02d}"

    try:
        path = Path(path_template.format(**template_values))
    except KeyError as error:
        missing_value = error.args[0]
        raise ValueError(
            f"Storage template '{storage_key}' requires {missing_value}"
        ) from error

    if path.is_absolute():
        return path

    return project_root / path
