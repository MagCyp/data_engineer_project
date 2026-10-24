from pathlib import Path

import pytest

from settings.config import (
    get_api_config,
    get_pipeline_config,
    get_storage_path,
    load_config,
    project_root,
)


def test_config():
    config = load_config()
    assert isinstance(config, dict)

    weather_api = config["apis"]["open_meteo_archive"]
    assert weather_api["base_url"] == (
        "https://archive-api.open-meteo.com/v1/archive"
    )
    assert config["http"] == {
        "timeout_seconds": 60,
        "max_retries": 3,
        "retry_base_delay_seconds": 1,
        "retry_max_delay_seconds": 60,
    }

    weather = config["pipelines"]["weather"]
    assert weather["api"] == "open_meteo_archive"
    assert weather["available_from"] == "1940-01-01"
    assert weather["default_city"] == "New York"
    assert config["storage"] == {
        "raw_path": "data/raw/{pipeline_name}",
        "bronze_path": (
            "data/bronze/{pipeline_name}/year={year}/month={month}"
        ),
        "silver_path": (
            "data/silver/{pipeline_name}/year={year}/month={month}"
        ),
        "bronze_reference_path": "data/bronze/{pipeline_name}/reference",
        "silver_reference_path": "data/silver/{pipeline_name}/reference",
    }

    assert weather["locations"]
    assert {
        "name": "New York",
        "latitude": 40.7128,
        "longitude": -74.006,
    } in weather["locations"]

    for item in weather["locations"]:
        assert "name" in item
        assert "latitude" in item
        assert "longitude" in item

    subway = config["pipelines"]["mta_subway"]
    assert subway["api"] == "ny_open_data"
    assert {
        dataset["resource_id"]
        for dataset in subway["datasets"].values()
    } == {"t69i-h2me", "wujg-7c2s", "5wq4-mkjj"}
    active_mobility = config["pipelines"]["active_mobility"]
    assert active_mobility == {
        "api": "nyc_open_data",
        "available_from": "2012-08-31",
        "counts_resource_id": "ct66-47at",
        "sensors_resource_id": "6up2-gnw8",
    }
    assert subway["available_from"] == "2017-01-13"


def test_get_named_api_and_pipeline_config() -> None:
    config = load_config()

    api = get_api_config(config, "ny_open_data")
    pipeline = get_pipeline_config(config, "mta_subway")

    assert api["base_url"] == "https://data.ny.gov/resource"
    assert api["response_format"] == "json"
    assert api["timeout_seconds"] == 60
    assert api["max_retries"] == 3
    assert pipeline["api"] == "ny_open_data"


def test_get_named_config_rejects_unknown_names() -> None:
    with pytest.raises(ValueError, match="API 'missing' is not configured"):
        get_api_config({"apis": {}}, "missing")

    with pytest.raises(
        ValueError,
        match="Pipeline 'missing' is not configured",
    ):
        get_pipeline_config({"pipelines": {}}, "missing")


def test_get_storage_path_resolves_relative_project_path() -> None:
    config = {
        "storage": {
            "custom_path": (
                "data/custom/{pipeline_name}/year={year}/month={month}"
            ),
        }
    }

    result = get_storage_path(
        config,
        storage_key="custom_path",
        pipeline_name="weather",
        year=2025,
        month=1,
    )

    assert result == (
        project_root
        / "data"
        / "custom"
        / "weather"
        / "year=2025"
        / "month=01"
    )


def test_get_storage_path_resolves_unpartitioned_raw_path() -> None:
    config = {"storage": {"raw_path": "data/raw/{pipeline_name}"}}

    result = get_storage_path(
        config,
        storage_key="raw_path",
        pipeline_name="bike",
    )

    assert result == project_root / "data" / "raw" / "bike"


def test_get_storage_path_requires_partition_values_from_template() -> None:
    config = {
        "storage": {
            "bronze_path": "data/bronze/{pipeline_name}/year={year}",
        }
    }

    with pytest.raises(ValueError, match="requires year"):
        get_storage_path(
            config,
            storage_key="bronze_path",
            pipeline_name="bike",
        )


def test_get_storage_path_keeps_absolute_path(tmp_path: Path) -> None:
    path_template = (
        tmp_path / "{pipeline_name}" / "year={year}" / "month={month}"
    )
    config = {"storage": {"custom_path": str(path_template)}}

    result = get_storage_path(
        config,
        storage_key="custom_path",
        pipeline_name="weather",
        year=2025,
        month=12,
    )

    assert result == tmp_path / "weather" / "year=2025" / "month=12"


@pytest.mark.parametrize("month", [0, 13])
def test_get_storage_path_rejects_invalid_month(month: int) -> None:
    config = {"storage": {"custom_path": "data/{year}/{month}"}}

    with pytest.raises(ValueError, match="month must be between 1 and 12"):
        get_storage_path(
            config,
            storage_key="custom_path",
            pipeline_name="weather",
            year=2025,
            month=month,
        )
