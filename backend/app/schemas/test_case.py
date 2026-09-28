from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class TestCasePublic(BaseModel):
    test_case_id: int
    input: str
    expected_output: str
    time_limit_override: Optional[float] = None
    memory_limit_override: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class TestCaseCreate(BaseModel):
    input: str
    expected_output: str
    is_hidden: bool = False
    time_limit_override: Optional[float] = None
    memory_limit_override: Optional[int] = None


class TestCaseUpdate(BaseModel):
    input: Optional[str] = None
    expected_output: Optional[str] = None
    is_hidden: Optional[bool] = None
    time_limit_override: Optional[float] = None
    memory_limit_override: Optional[int] = None


class TestCaseAdminResponse(BaseModel):
    test_case_id: int
    problem_id: int
    input: str
    expected_output: str
    is_hidden: bool
    time_limit_override: Optional[float] = None
    memory_limit_override: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
