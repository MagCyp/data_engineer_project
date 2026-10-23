from datetime import date

import pytest

from orchestration import cli


@pytest.fixture
def validated_ranges(
    monkeypatch: pytest.MonkeyPatch,
) -> list[tuple[date, date]]:
    captured: list[tuple[date, date]] = []

    def validate(
        config: object,
        *,
        start_date: date,
        end_date: date,
        app_token: str | None = None,
    ) -> date:
        captured.append((start_date, end_date))
        return date(2026, 10, 14)

    monkeypatch.setattr(cli, "load_config", lambda: {})
    monkeypatch.setattr(cli, "validate_mobility_date_range", validate)
    monkeypatch.setattr(cli, "_get_socrata_app_token", lambda: None)
    return captured


def test_validate_month_range_prints_resolved_dates_for_airflow(
    validated_ranges: list[tuple[date, date]],
    capsys: pytest.CaptureFixture[str],
) -> None:
    result = cli.main(
        [
            "validate-month-range",
            "--start-month",
            "2026-08",
            "--end-month",
            "2026-09",
        ]
    )

    assert result == 0
    assert validated_ranges == [(date(2026, 8, 1), date(2026, 9, 30))]
    assert capsys.readouterr().out.splitlines()[-1] == (
        "2026-08-01 2026-09-30"
    )


def test_validate_year_range_prints_resolved_dates_for_airflow(
    validated_ranges: list[tuple[date, date]],
    capsys: pytest.CaptureFixture[str],
) -> None:
    result = cli.main(
        [
            "validate-year-range",
            "--start-year",
            "2024",
            "--end-year",
            "2025",
        ]
    )

    assert result == 0
    assert validated_ranges == [(date(2024, 1, 1), date(2025, 12, 31))]
    assert capsys.readouterr().out.splitlines()[-1] == (
        "2024-01-01 2025-12-31"
    )
