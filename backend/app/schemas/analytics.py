from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class OverviewAnalytics(BaseModel):
    total_problems_attempted: int
    total_problems_solved: int
    total_submissions: int
    successful_submissions: int
    failed_submissions: int
    success_rate: float
    current_streak: int
    longest_streak: int
    xp: int
    current_level: int

    model_config = ConfigDict(from_attributes=True)


class DiagnosticSummaryAnalytics(BaseModel):
    has_completed_diagnostic: bool
    score: Optional[float] = None
    total_questions: Optional[int] = None
    correct_answers: Optional[int] = None
    percentage: Optional[float] = None
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class TopicSkillItemAnalytics(BaseModel):
    topic_id: int
    topic_name: str
    skill_score: float
    skill_level: str
    confidence: float
    problems_solved: int
    total_points: int

    model_config = ConfigDict(from_attributes=True)


class SubmissionItemAnalytics(BaseModel):
    submission_id: int
    problem_id: int
    problem_title: str
    language: str
    status: str
    submitted_at: datetime
    execution_time_ms: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class SubmissionAnalytics(BaseModel):
    total_submissions: int
    passed_submissions: int
    failed_submissions: int
    success_rate: float
    recent_submissions: List[SubmissionItemAnalytics] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class RecommendationItemAnalytics(BaseModel):
    recommendation_id: Optional[int] = None
    problem_id: int
    problem_title: str
    rank: int
    score: float
    reasons: List[str] = Field(default_factory=list)
    difficulty: str

    model_config = ConfigDict(from_attributes=True)


class RecommendationSummaryAnalytics(BaseModel):
    total_recommendations: int
    recommendations: List[RecommendationItemAnalytics] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class GamificationSummaryAnalytics(BaseModel):
    xp: int
    level: int
    problems_solved: int
    successful_submissions: int
    current_streak: int
    longest_streak: int
    badges: List[str] = Field(default_factory=list)
    xp_for_next_level: int
    last_activity_date: Optional[date] = None

    model_config = ConfigDict(from_attributes=True)


class DashboardResponse(BaseModel):
    overview: OverviewAnalytics
    diagnostic: DiagnosticSummaryAnalytics
    skills: List[TopicSkillItemAnalytics] = Field(default_factory=list)
    submissions: SubmissionAnalytics
    recommendations: RecommendationSummaryAnalytics
    gamification: GamificationSummaryAnalytics

    model_config = ConfigDict(from_attributes=True)
