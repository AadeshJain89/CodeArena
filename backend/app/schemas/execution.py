from typing import List, Optional
from pydantic import BaseModel, Field


class ExecutionRequest(BaseModel):
    problem_id: int = Field(..., description="Target problem ID")
    language: str = Field(..., description="Programming language ('python' or 'cpp')")
    source_code: str = Field(..., description="Untrusted source code submitted for execution")


class TestResultItem(BaseModel):
    test_number: int
    status: str
    is_hidden: bool
    execution_time_ms: float
    actual_output: Optional[str] = None
    expected_output: Optional[str] = None
    error_message: Optional[str] = None


class ExecutionResponse(BaseModel):
    status: str
    language: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    execution_time_ms: float
    memory_used_mb: float
    test_results: List[TestResultItem]
