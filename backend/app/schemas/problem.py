from datetime import datetime
from typing import List, Optional, Any
from pydantic import BaseModel, ConfigDict
from app.models.problem import ProblemDifficulty
from app.schemas.topic import TopicResponse
from app.schemas.test_case import TestCasePublic


class ProblemListItem(BaseModel):
    id: int
    title: str
    slug: str
    difficulty: ProblemDifficulty
    topics: List[TopicResponse] = []
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
    topics: List[TopicResponse] = []
    public_test_cases: List[TestCasePublic] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaginatedProblemResponse(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    items: List[ProblemListItem]
