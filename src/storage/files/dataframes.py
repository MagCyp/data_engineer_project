from collections.abc import Iterable, Mapping
from typing import Any

import polars as pl
from pydantic import BaseModel


def models_to_dataframe[ModelT: BaseModel](
    models: Iterable[ModelT],
    *,
    schema: Mapping[str, Any] | None = None,
) -> pl.DataFrame:
    """Convert Pydantic models into a Polars DataFrame."""
    rows = [model.model_dump(mode="python") for model in models]

    if not rows and schema is None:
        return pl.DataFrame()

    if not rows:
        return pl.DataFrame(schema=schema)

    return pl.from_dicts(rows, schema=schema, strict=True)
