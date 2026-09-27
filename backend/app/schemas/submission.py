from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class SubmissionCreate(BaseModel):
    problem_id: int
    language: str
    source_code: str


class SubmissionTestResultResponse(BaseModel):
    id: int
    test_case_id: int
    status: str
    execution_time_ms: float
    actual_output: Optional[str] = None
    expected_output: Optional[str] = None
    error_message: Optional[str] = None
    is_hidden: bool = False

    model_config = ConfigDict(from_attributes=True)


class SubmissionResponse(BaseModel):
    id: int
    user_id: int
    problem_id: int
    problem_title: Optional[str] = None
    language: str
    source_code: str
    status: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    execution_time_ms: float
    memory_used_mb: float
    created_at: datetime
    test_results: List[SubmissionTestResultResponse] = []

    model_config = ConfigDict(from_attributes=True)


class SubmissionSummaryResponse(BaseModel):
    id: int
    problem_id: int
    problem_title: Optional[str] = None
    language: str
    status: str
    passed_tests: int
    total_tests: int
    execution_time_ms: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
