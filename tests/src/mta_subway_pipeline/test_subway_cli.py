from datetime import date
from unittest.mock import Mock

import pytest

from mta_subway_pipeline import cli


def test_main_runs_pipeline_in_order(monkeypatch: pytest.MonkeyPatch) -> None:
    config: dict[str, object] = {}
    calls: list[str] = []
    backfill_subway = Mock(
        side_effect=lambda **kwargs: calls.append("backfill")
    )
    load_subway_range = Mock(
        side_effect=lambda **kwargs: calls.append("warehouse")
    )
    monkeypatch.setattr(cli, "load_config", Mock(return_value=config))
    load_dotenv = Mock()
    monkeypatch.setattr(cli, "load_dotenv", load_dotenv)
    monkeypatch.setattr(cli, "backfill_subway", backfill_subway)
    monkeypatch.setattr(cli, "load_subway_range", load_subway_range)
    monkeypatch.setenv("SOCRATA_APP_TOKEN", "token")

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
    load_dotenv.assert_called_once_with()
    assert calls == ["backfill", "warehouse"]
    backfill_subway.assert_called_once_with(
        config=config,
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 31),
        page_size=1_000,
        app_token="token",
    )
    load_subway_range.assert_called_once_with(
        config=config,
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 31),
    )


@pytest.mark.parametrize("app_token", [None, "", "   "])
def test_main_allows_ingestion_without_app_token(
    monkeypatch: pytest.MonkeyPatch,
    app_token: str | None,
) -> None:
    backfill_subway = Mock()
    monkeypatch.setattr(cli, "load_dotenv", Mock())
    monkeypatch.setattr(cli, "load_config", Mock(return_value={}))
    monkeypatch.setattr(cli, "backfill_subway", backfill_subway)
    if app_token is None:
        monkeypatch.delenv("SOCRATA_APP_TOKEN", raising=False)
    else:
        monkeypatch.setenv("SOCRATA_APP_TOKEN", app_token)

    result = cli.main(
        [
            "backfill",
            "--start-date",
            "2025-01-01",
            "--end-date",
            "2025-01-31",
        ]
    )

    assert result == 0
    backfill_subway.assert_called_once_with(
        config={},
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 31),
        page_size=50_000,
        app_token=None,
    )


def test_main_does_not_require_app_token_for_warehouse(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config: dict[str, object] = {}
    load_subway_range = Mock()
    monkeypatch.setattr(cli, "load_dotenv", Mock())
    monkeypatch.setattr(cli, "load_config", Mock(return_value=config))
    monkeypatch.setattr(cli, "load_subway_range", load_subway_range)
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
    load_subway_range.assert_called_once_with(
        config=config,
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 31),
    )
