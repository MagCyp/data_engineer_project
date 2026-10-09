from pydantic import BaseModel

from storage.dataframes import models_to_dataframe


class ExampleRecord(BaseModel):
    pipeline: str
    value: int


def test_models_to_dataframe_supports_other_pipeline_models() -> None:
    records = [ExampleRecord(pipeline="air_quality", value=42)]

    result = models_to_dataframe(records)

    assert result.to_dicts() == [{"pipeline": "air_quality", "value": 42}]
