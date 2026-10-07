from settings.config import load_config


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
