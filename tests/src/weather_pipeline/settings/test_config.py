from pathlib import Path

import pytest

from settings.config import get_storage_path, load_config, project_root


def test_config():
    config = load_config()
    assert isinstance(config, dict)

    assert config["api"]["base_url"] == (
        "https://archive-api.open-meteo.com/v1/archive"
    )
    assert config["api"]["timeout_seconds"] == 30
    assert config["default_city"] == "New York"

    assert config["locations"]
    assert {
        "name": "New York",
        "latitude": 40.7128,
        "longitude": -74.006,
    } in config["locations"]

    for item in config["locations"]:
        assert "name" in item
        assert "latitude" in item
        assert "longitude" in item


def test_get_storage_path_resolves_relative_project_path() -> None:
    config = {
        "storage": {
            "custom_path": "data/custom/year={year}/month={month}",
        }
    }

    result = get_storage_path(
        config,
        storage_key="custom_path",
        year=2025,
        month=1,
    )

    assert result == (
        project_root / "data" / "custom" / "year=2025" / "month=01"
    )


def test_get_storage_path_keeps_absolute_path(tmp_path: Path) -> None:
    path_template = tmp_path / "year={year}" / "month={month}"
    config = {"storage": {"custom_path": str(path_template)}}

    result = get_storage_path(
        config,
        storage_key="custom_path",
        year=2025,
        month=12,
    )

    assert result == tmp_path / "year=2025" / "month=12"


@pytest.mark.parametrize("month", [0, 13])
def test_get_storage_path_rejects_invalid_month(month: int) -> None:
    config = {"storage": {"custom_path": "data/{year}/{month}"}}

    with pytest.raises(ValueError, match="month must be between 1 and 12"):
        get_storage_path(
            config,
            storage_key="custom_path",
            year=2025,
            month=month,
        )
