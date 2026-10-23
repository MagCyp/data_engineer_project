from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

from helpers import validate_date_range
from mta_subway_pipeline.ingestion.client import (
    SOCRATA_DEFAULT_MAX_RETRIES,
    SOCRATA_DEFAULT_RETRY_BASE_DELAY_SECONDS,
    SOCRATA_DEFAULT_RETRY_MAX_DELAY_SECONDS,
    SOCRATA_MAX_PAGE_SIZE,
    get_latest_subway_date,
    iter_subway_data,
)
from mta_subway_pipeline.validation.models import SubwaySourceRecord
from settings import get_api_config, get_pipeline_config


@dataclass(frozen=True, slots=True)
class SubwayDatasetSlice:
    name: str
    resource_id: str
    start_date: date
    end_date: date


def _year(
    value: object,
    *,
    field_name: str,
    dataset_name: str,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(
            f"Subway dataset '{dataset_name}' field '{field_name}' "
            "must be an integer"
        )
    if not 1 <= value <= 9999:
        raise ValueError(
            f"Subway dataset '{dataset_name}' field '{field_name}' "
            "must be between 1 and 9999"
        )
    return value


def _configured_datasets(
    pipeline_config: Mapping[str, Any],
) -> list[SubwayDatasetSlice]:
    configured = pipeline_config.get("datasets")
    if not isinstance(configured, Mapping) or not configured:
        raise ValueError("Subway datasets must be a non-empty mapping")

    datasets: list[SubwayDatasetSlice] = []
    for dataset_name, raw_config in configured.items():
        name = str(dataset_name)
        if not isinstance(raw_config, Mapping):
            raise ValueError(f"Subway dataset '{name}' must be a mapping")

        resource_id = raw_config.get("resource_id")
        if not isinstance(resource_id, str) or not resource_id.strip():
            raise ValueError(
                f"Subway dataset '{name}' must define a resource_id"
            )

        start_year = _year(
            raw_config.get("start_year"),
            field_name="start_year",
            dataset_name=name,
        )
        raw_end_year = raw_config.get("end_year")
        end_year = (
            None
            if raw_end_year is None
            else _year(
                raw_end_year,
                field_name="end_year",
                dataset_name=name,
            )
        )
        if end_year is not None and end_year < start_year:
            raise ValueError(
                f"Subway dataset '{name}' end_year must not precede start_year"
            )

        datasets.append(
            SubwayDatasetSlice(
                name=name,
                resource_id=resource_id.strip(),
                start_date=date(start_year, 1, 1),
                end_date=(
                    date.max if end_year is None else date(end_year, 12, 31)
                ),
            )
        )

    datasets.sort(key=lambda dataset: dataset.start_date)
    for previous, current in zip(datasets, datasets[1:], strict=False):
        if current.start_date <= previous.end_date:
            raise ValueError(
                "Subway dataset date ranges overlap: "
                f"'{previous.name}' and '{current.name}'"
            )

    return datasets


def _dataset_slices(
    pipeline_config: Mapping[str, Any],
    *,
    start_date: date,
    end_date: date,
) -> list[SubwayDatasetSlice]:
    validate_date_range(start_date, end_date)

    cursor = start_date
    slices: list[SubwayDatasetSlice] = []

    for dataset in _configured_datasets(pipeline_config):
        if dataset.end_date < start_date or dataset.start_date > end_date:
            continue

        slice_start = max(start_date, dataset.start_date)
        slice_end = min(end_date, dataset.end_date)
        if slice_start > cursor:
            missing_end = slice_start - timedelta(days=1)
            raise ValueError(
                f"No subway dataset covers {cursor} through {missing_end}"
            )

        slices.append(
            SubwayDatasetSlice(
                name=dataset.name,
                resource_id=dataset.resource_id,
                start_date=slice_start,
                end_date=slice_end,
            )
        )
        if slice_end == end_date:
            return slices
        cursor = slice_end + timedelta(days=1)

    raise ValueError(f"No subway dataset covers {cursor} through {end_date}")


def get_subway_dataset_slices(
    config: Mapping[str, Any],
    *,
    start_date: date,
    end_date: date,
) -> list[SubwayDatasetSlice]:
    pipeline_config = get_pipeline_config(config, "mta_subway")
    return _dataset_slices(
        pipeline_config,
        start_date=start_date,
        end_date=end_date,
    )


def iter_subway_records(
    config: Mapping[str, Any],
    *,
    start_date: date,
    end_date: date,
    page_size: int = SOCRATA_MAX_PAGE_SIZE,
    app_token: str | None = None,
) -> Iterator[SubwaySourceRecord]:
    pipeline_config = get_pipeline_config(config, "mta_subway")
    api_name = pipeline_config.get("api")
    if not isinstance(api_name, str) or not api_name.strip():
        raise ValueError("Subway pipeline must reference an API")
    api_config = get_api_config(config, api_name)

    dataset_slices = _dataset_slices(
        pipeline_config,
        start_date=start_date,
        end_date=end_date,
    )
    open_resource_ids = {
        dataset.resource_id
        for dataset in _configured_datasets(pipeline_config)
        if dataset.end_date == date.max
    }
    for dataset_slice in dataset_slices:
        if dataset_slice.resource_id not in open_resource_ids:
            continue
        latest_date = get_latest_subway_date(
            resource_id=dataset_slice.resource_id,
            base_url=str(api_config["base_url"]),
            timeout_seconds=int(api_config["timeout_seconds"]),
            response_format=str(api_config.get("response_format", "json")),
            app_token=app_token,
            max_retries=api_config.get(
                "max_retries",
                SOCRATA_DEFAULT_MAX_RETRIES,
            ),
            retry_base_delay_seconds=api_config.get(
                "retry_base_delay_seconds",
                SOCRATA_DEFAULT_RETRY_BASE_DELAY_SECONDS,
            ),
            retry_max_delay_seconds=api_config.get(
                "retry_max_delay_seconds",
                SOCRATA_DEFAULT_RETRY_MAX_DELAY_SECONDS,
            ),
        )
        if latest_date is None:
            raise ValueError(
                f"Subway dataset '{dataset_slice.name}' contains no data"
            )
        if dataset_slice.end_date > latest_date:
            raise ValueError(
                f"end_date {dataset_slice.end_date} exceeds the latest "
                f"available subway date {latest_date}"
            )

    for dataset_slice in dataset_slices:
        yield from iter_subway_data(
            resource_id=dataset_slice.resource_id,
            base_url=str(api_config["base_url"]),
            timeout_seconds=int(api_config["timeout_seconds"]),
            start_date=dataset_slice.start_date,
            end_date=dataset_slice.end_date,
            response_format=str(api_config.get("response_format", "json")),
            page_size=page_size,
            app_token=app_token,
            max_retries=api_config.get(
                "max_retries",
                SOCRATA_DEFAULT_MAX_RETRIES,
            ),
            retry_base_delay_seconds=api_config.get(
                "retry_base_delay_seconds",
                SOCRATA_DEFAULT_RETRY_BASE_DELAY_SECONDS,
            ),
            retry_max_delay_seconds=api_config.get(
                "retry_max_delay_seconds",
                SOCRATA_DEFAULT_RETRY_MAX_DELAY_SECONDS,
            ),
        )


def fetch_subway_data(
    config: Mapping[str, Any],
    *,
    start_date: date,
    end_date: date,
    page_size: int = SOCRATA_MAX_PAGE_SIZE,
    app_token: str | None = None,
) -> list[SubwaySourceRecord]:
    return list(
        iter_subway_records(
            config,
            start_date=start_date,
            end_date=end_date,
            page_size=page_size,
            app_token=app_token,
        )
    )
