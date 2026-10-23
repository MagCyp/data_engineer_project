from datetime import date
from unittest.mock import Mock

import pytest

from active_mobility_pipeline import cli


def test_pipeline_runs_backfill_before_warehouse(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config: dict[str, object] = {}
    calls: list[str] = []
    backfill = Mock(side_effect=lambda **kwargs: calls.append("backfill"))
    warehouse = Mock(side_effect=lambda **kwargs: calls.append("warehouse"))
    monkeypatch.setattr(cli, "load_dotenv", Mock())
    monkeypatch.setattr(cli, "load_config", Mock(return_value=config))
    monkeypatch.setattr(cli, "backfill_active_mobility", backfill)
    monkeypatch.setattr(cli, "load_active_mobility_range", warehouse)
    monkeypatch.setenv("SOCRATA_APP_TOKEN", " token ")

    result = cli.main(
        [
            "pipeline",
            "--start-date",
            "2025-01-01",
            "--end-date",
            "2025-01-31",
            "--page-size",
            "1000",
        ]
    )

    assert result == 0
    assert calls == ["backfill", "warehouse"]
    backfill.assert_called_once_with(
        config=config,
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 31),
        page_size=1000,
        app_token="token",
    )
    warehouse.assert_called_once_with(
        config=config,
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 31),
    )


def test_warehouse_does_not_require_app_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config: dict[str, object] = {}
    backfill = Mock()
    warehouse = Mock()
    monkeypatch.setattr(cli, "load_dotenv", Mock())
    monkeypatch.setattr(cli, "load_config", Mock(return_value=config))
    monkeypatch.setattr(cli, "backfill_active_mobility", backfill)
    monkeypatch.setattr(cli, "load_active_mobility_range", warehouse)
    monkeypatch.delenv("SOCRATA_APP_TOKEN", raising=False)

    result = cli.main(
        [
            "warehouse",
            "--start-date",
            "2025-01-01",
            "--end-date",
            "2025-01-31",
        ]
    )

    assert result == 0
    backfill.assert_not_called()
    warehouse.assert_called_once()

