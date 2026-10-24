from datetime import date
from unittest.mock import Mock

import pytest

from active_mobility_pipeline.ingestion import service


def make_config() -> dict[str, object]:
    return {
        "http": {
            "timeout_seconds": 60,
            "max_retries": 3,
            "retry_base_delay_seconds": 1,
            "retry_max_delay_seconds": 60,
        },
        "apis": {
            "nyc_open_data": {
                "base_url": "https://data.cityofnewyork.us/resource",
                "response_format": "json",
            }
        },
        "pipelines": {
            "active_mobility": {
                "api": "nyc_open_data",
                "counts_resource_id": "ct66-47at",
            }
        },
    }


def test_get_latest_available_date_uses_counts_dataset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    latest_date = Mock(return_value=date(2026, 10, 23))
    monkeypatch.setattr(service, "get_latest_socrata_date", latest_date)

    result = service.get_latest_available_date(
        make_config(),
        app_token="token",
    )

    assert result == date(2026, 10, 23)
    latest_date.assert_called_once_with(
        resource_id="ct66-47at",
        timestamp_field="timestamp",
        app_token="token",
        base_url="https://data.cityofnewyork.us/resource",
        timeout_seconds=60,
        response_format="json",
        max_retries=3,
        retry_base_delay_seconds=1,
        retry_max_delay_seconds=60,
    )
