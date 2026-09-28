from datetime import datetime
from typing import List, Optional, Any
from pydantic import BaseModel, ConfigDict, Field
from app.models.problem import ProblemDifficulty
from app.schemas.topic import TopicResponse
from app.schemas.test_case import TestCasePublic, TestCaseAdminResponse


class ProblemListItem(BaseModel):
    id: int
    title: str
    slug: str
    difficulty: ProblemDifficulty
    topics: List[TopicResponse] = Field(default_factory=list)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProblemDetail(BaseModel):
    id: int
    title: str
    slug: str
    description: str
    difficulty: ProblemDifficulty
    constraints: Optional[str] = None
    input_format: Optional[str] = None
    output_format: Optional[str] = None
    examples: Optional[Any] = None
    starter_code: Optional[Any] = None
    solution_language_support: Optional[Any] = None
    topics: List[TopicResponse] = Field(default_factory=list)
    public_test_cases: List[TestCasePublic] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProblemCreate(BaseModel):
    title: str
    slug: Optional[str] = None
    description: str
    difficulty: ProblemDifficulty
    constraints: Optional[str] = None
    input_format: Optional[str] = None
    output_format: Optional[str] = None
    examples: Optional[Any] = None
    starter_code: Optional[Any] = None
    solution_language_support: Optional[Any] = None
    is_diagnostic: bool = False
    diagnostic_options: Optional[Any] = None
    diagnostic_correct_option: Optional[str] = None
    question_type: Optional[str] = "CODING"
    options: Optional[Any] = None
    correct_option: Optional[str] = None
    topic_ids: List[int] = Field(default_factory=list)


class ProblemUpdate(BaseModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    difficulty: Optional[ProblemDifficulty] = None
    constraints: Optional[str] = None
    input_format: Optional[str] = None
    output_format: Optional[str] = None
    examples: Optional[Any] = None
    starter_code: Optional[Any] = None
    solution_language_support: Optional[Any] = None
    is_diagnostic: Optional[bool] = None
    diagnostic_options: Optional[Any] = None
    diagnostic_correct_option: Optional[str] = None
    question_type: Optional[str] = None
    options: Optional[Any] = None
    correct_option: Optional[str] = None
    topic_ids: Optional[List[int]] = None


class AdminProblemDetail(BaseModel):
    id: int
    title: str
    slug: str
    description: str
    difficulty: ProblemDifficulty
    constraints: Optional[str] = None
    input_format: Optional[str] = None
    output_format: Optional[str] = None
    examples: Optional[Any] = None
    starter_code: Optional[Any] = None
    solution_language_support: Optional[Any] = None
    is_diagnostic: bool
    diagnostic_options: Optional[Any] = None
    diagnostic_correct_option: Optional[str] = None
    question_type: Optional[str] = None
    options: Optional[Any] = None
    correct_option: Optional[str] = None
    topics: List[TopicResponse] = Field(default_factory=list)
    test_cases: List[TestCaseAdminResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaginatedProblemResponse(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    items: List[ProblemListItem]
