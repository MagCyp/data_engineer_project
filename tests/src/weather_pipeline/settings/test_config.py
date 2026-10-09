from pathlib import Path

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
    config = {"storage": {"custom_path": "data/custom"}}

    result = get_storage_path(config, "custom_path")

    assert result == project_root / "data" / "custom"


def test_get_storage_path_keeps_absolute_path(tmp_path: Path) -> None:
    config = {"storage": {"custom_path": str(tmp_path)}}

    result = get_storage_path(config, "custom_path")

    assert result == tmp_path
