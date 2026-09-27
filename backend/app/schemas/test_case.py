from datetime import datetime
from pydantic import BaseModel, ConfigDict


class TestCasePublic(BaseModel):
    test_case_id: int
    input: str
    expected_output: str
    time_limit_override: float | None = None
    memory_limit_override: int | None = None

    model_config = ConfigDict(from_attributes=True)
