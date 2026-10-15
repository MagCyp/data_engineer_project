import importlib

import pytest

BIKE_PIPELINE_MODULES = (
    "bike_pipeline.backfill",
    "bike_pipeline.cli",
    "bike_pipeline.ingestion.reader",
    "bike_pipeline.ingestion.service",
    "bike_pipeline.load",
    "bike_pipeline.pipeline",
    "bike_pipeline.transformations.bronze",
    "bike_pipeline.transformations.silver",
    "bike_pipeline.validation.bronze",
    "bike_pipeline.validation.models",
    "bike_pipeline.validation.silver",
    "bike_pipeline.warehouse",
)


@pytest.mark.parametrize("module_name", BIKE_PIPELINE_MODULES)
def test_bike_pipeline_module_can_be_imported(module_name: str) -> None:
    assert importlib.import_module(module_name) is not None
