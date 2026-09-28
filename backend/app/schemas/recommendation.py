from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class TopicSummaryResponse(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class RecommendationProblemSummary(BaseModel):
    id: int
    title: str
    slug: str
    difficulty: str
    description: str
    topics: List[TopicSummaryResponse] = []

    model_config = ConfigDict(from_attributes=True)


class RecommendationResponse(BaseModel):
    recommendation_id: int
    user_id: int
    problem_id: int
    rank: int
    score: float
    reasons: List[str]
    generated_at: datetime
    problem: RecommendationProblemSummary

    model_config = ConfigDict(from_attributes=True)
