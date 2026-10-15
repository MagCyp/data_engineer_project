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


def get_api_config(
    config: Mapping[str, Any],
    api_name: str,
) -> Mapping[str, Any]:
    """Return configuration for a named external API."""
    apis = config.get("apis")
    if not isinstance(apis, Mapping) or api_name not in apis:
        raise ValueError(f"API '{api_name}' is not configured")

    api_config = apis[api_name]
    if not isinstance(api_config, Mapping):
        raise ValueError(f"API '{api_name}' configuration must be a mapping")
    return api_config


def get_pipeline_config(
    config: Mapping[str, Any],
    pipeline_name: str,
) -> Mapping[str, Any]:
    """Return configuration for a named data pipeline."""
    pipelines = config.get("pipelines")
    if not isinstance(pipelines, Mapping) or pipeline_name not in pipelines:
        raise ValueError(f"Pipeline '{pipeline_name}' is not configured")

    pipeline_config = pipelines[pipeline_name]
    if not isinstance(pipeline_config, Mapping):
        raise ValueError(
            f"Pipeline '{pipeline_name}' configuration must be a mapping"
        )
    return pipeline_config


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

    path_template = str(config["storage"][storage_key])
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
