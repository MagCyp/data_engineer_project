from collections.abc import Mapping, Sequence
from typing import Any

import polars as pl
from pydantic import BaseModel


def models_to_dataframe[ModelT: BaseModel](
    models: Sequence[ModelT],
    *,
    schema: Mapping[str, Any] | None = None,
) -> pl.DataFrame:
    """Convert any sequence of Pydantic models into a Polars DataFrame."""
    rows = [model.model_dump() for model in models]

    if not rows and schema is None:
        return pl.DataFrame()

    return pl.DataFrame(rows, schema=schema)
