import importlib

import pytest

MODULES = (
    "active_mobility_pipeline.backfill",
    "active_mobility_pipeline.cli",
    "active_mobility_pipeline.ingestion.client",
    "active_mobility_pipeline.ingestion.service",
    "active_mobility_pipeline.load",
    "active_mobility_pipeline.pipeline",
    "active_mobility_pipeline.transformations.bronze",
    "active_mobility_pipeline.transformations.silver",
    "active_mobility_pipeline.validation.bronze",
    "active_mobility_pipeline.validation.models",
    "active_mobility_pipeline.validation.silver",
    "active_mobility_pipeline.warehouse",
)


@pytest.mark.parametrize("module_name", MODULES)
def test_active_mobility_module_can_be_imported(module_name: str) -> None:
    assert importlib.import_module(module_name) is not None
