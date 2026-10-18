from datetime import date
from unittest.mock import Mock, call

import pytest

from mta_subway_pipeline.ingestion import service
from mta_subway_pipeline.validation.models import SubwaySourceRecord


def make_config() -> dict[str, object]:
    return {
        "apis": {
            "ny_open_data": {
                "base_url": "https://data.ny.gov/resource",
                "response_format": "json",
                "timeout_seconds": 60,
                "max_retries": 3,
                "retry_base_delay_seconds": 1,
                "retry_max_delay_seconds": 60,
            }
        },
        "pipelines": {
            "mta_subway": {
                "api": "ny_open_data",
                "datasets": {
                    "hourly_ridership_2017_2019": {
                        "resource_id": "t69i-h2me",
                        "start_year": 2017,
                        "end_year": 2019,
                        "incremental": False,
                    },
                    "hourly_ridership_2020_2024": {
                        "resource_id": "wujg-7c2s",
                        "start_year": 2020,
                        "end_year": 2024,
                        "incremental": False,
                    },
                    "hourly_ridership_2025_present": {
                        "resource_id": "5wq4-mkjj",
                        "start_year": 2025,
                        "end_year": None,
                        "incremental": True,
                    },
                },
            }
        },
    }


def test_get_subway_dataset_slices_splits_range_between_resources() -> None:
    slices = service.get_subway_dataset_slices(
        make_config(),
        start_date=date(2019, 12, 31),
        end_date=date(2020, 1, 2),
    )

    assert [dataset.resource_id for dataset in slices] == [
        "t69i-h2me",
        "wujg-7c2s",
    ]
    assert (slices[0].start_date, slices[0].end_date) == (
        date(2019, 12, 31),
        date(2019, 12, 31),
    )
    assert (slices[1].start_date, slices[1].end_date) == (
        date(2020, 1, 1),
        date(2020, 1, 2),
    )


def test_open_dataset_shifts_end_date_when_it_is_in_current_week(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(service, "_current_date", lambda: date(2026, 10, 17))

    slices = service.get_subway_dataset_slices(
        make_config(),
        start_date=date(2026, 10, 1),
        end_date=date(2026, 10, 17),
    )

    assert len(slices) == 1
    assert slices[0].resource_id == "5wq4-mkjj"
    assert slices[0].end_date == date(2026, 10, 10)


def test_open_dataset_keeps_end_date_from_previous_week(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(service, "_current_date", lambda: date(2026, 10, 17))

    slices = service.get_subway_dataset_slices(
        make_config(),
        start_date=date(2026, 10, 1),
        end_date=date(2026, 10, 11),
    )

    assert len(slices) == 1
    assert slices[0].end_date == date(2026, 10, 11)


def test_open_dataset_returns_no_slice_when_shift_precedes_start(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(service, "_current_date", lambda: date(2026, 10, 17))

    assert service.get_subway_dataset_slices(
        make_config(),
        start_date=date(2026, 10, 12),
        end_date=date(2026, 10, 17),
    ) == []


def test_fetch_subway_data_delegates_each_slice_to_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first_record = Mock(spec=SubwaySourceRecord)
    second_record = Mock(spec=SubwaySourceRecord)
    iter_dataset = Mock(
        side_effect=[iter([first_record]), iter([second_record])]
    )
    monkeypatch.setattr(service, "iter_subway_data", iter_dataset)

    records = service.fetch_subway_data(
        make_config(),
        start_date=date(2024, 12, 31),
        end_date=date(2025, 1, 1),
        page_size=1000,
        app_token="token",
    )

    assert records == [first_record, second_record]
    assert iter_dataset.call_args_list == [
        call(
            resource_id="wujg-7c2s",
            base_url="https://data.ny.gov/resource",
            timeout_seconds=60,
            start_date=date(2024, 12, 31),
            end_date=date(2024, 12, 31),
            response_format="json",
            page_size=1000,
            app_token="token",
            max_retries=3,
            retry_base_delay_seconds=1,
            retry_max_delay_seconds=60,
        ),
        call(
            resource_id="5wq4-mkjj",
            base_url="https://data.ny.gov/resource",
            timeout_seconds=60,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 1),
            response_format="json",
            page_size=1000,
            app_token="token",
            max_retries=3,
            retry_base_delay_seconds=1,
            retry_max_delay_seconds=60,
        ),
    ]


def test_get_subway_dataset_slices_rejects_uncovered_range() -> None:
    with pytest.raises(
        ValueError,
        match="No subway dataset covers 2016-12-31 through 2016-12-31",
    ):
        service.get_subway_dataset_slices(
            make_config(),
            start_date=date(2016, 12, 31),
            end_date=date(2017, 1, 1),
        )


def test_get_subway_dataset_slices_rejects_overlapping_configuration() -> None:
    config = make_config()
    pipeline = config["pipelines"]["mta_subway"]
    pipeline["datasets"]["hourly_ridership_2020_2024"]["start_year"] = 2019

    with pytest.raises(ValueError, match="date ranges overlap"):
        service.get_subway_dataset_slices(
            config,
            start_date=date(2019, 1, 1),
            end_date=date(2019, 1, 2),
        )
