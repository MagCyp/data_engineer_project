from datetime import date

import pytest

from orchestration import date_range_validation


def make_config() -> dict[str, object]:
    return {
        "pipelines": {
            "weather": {"available_from": "1940-01-01"},
            "active_mobility": {"available_from": "2012-08-31"},
            "mta_subway": {"available_from": "2017-01-13"},
        }
    }


def set_latest_dates(
    monkeypatch: pytest.MonkeyPatch,
    *,
    active_mobility: date = date(2026, 10, 23),
    subway: date = date(2026, 10, 14),
) -> None:
    monkeypatch.setattr(
        date_range_validation,
        "get_latest_active_mobility_date",
        lambda config, app_token=None: active_mobility,
    )
    monkeypatch.setattr(
        date_range_validation,
        "get_latest_subway_date",
        lambda config, app_token=None: subway,
    )


def test_validate_mobility_date_range_accepts_partial_range(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    set_latest_dates(monkeypatch)

    latest_common_date = (
        date_range_validation.validate_mobility_date_range(
            make_config(),
            start_date=date(2026, 10, 1),
            end_date=date(2026, 10, 3),
        )
    )

    assert latest_common_date == date(2026, 10, 14)


def test_validate_mobility_date_range_accepts_multiple_months(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    set_latest_dates(monkeypatch)

    latest_common_date = (
        date_range_validation.validate_mobility_date_range(
            make_config(),
            start_date=date(2026, 8, 20),
            end_date=date(2026, 10, 3),
        )
    )

    assert latest_common_date == date(2026, 10, 14)


def test_validate_mobility_date_range_rejects_reversed_range(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    set_latest_dates(monkeypatch)

    with pytest.raises(ValueError, match="less than or equal to end_date"):
        date_range_validation.validate_mobility_date_range(
            make_config(),
            start_date=date(2026, 10, 3),
            end_date=date(2026, 10, 1),
        )


def test_validate_mobility_date_range_rejects_date_before_common_boundary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    set_latest_dates(monkeypatch)

    with pytest.raises(ValueError, match="common source boundary 2017-01-13"):
        date_range_validation.validate_mobility_date_range(
            make_config(),
            start_date=date(2017, 1, 1),
            end_date=date(2017, 1, 31),
        )


def test_validate_mobility_date_range_rejects_unpublished_end_date(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    set_latest_dates(monkeypatch)

    with pytest.raises(
        ValueError,
        match="latest common source date 2026-10-14",
    ):
        date_range_validation.validate_mobility_date_range(
            make_config(),
            start_date=date(2026, 10, 1),
            end_date=date(2026, 10, 15),
        )
