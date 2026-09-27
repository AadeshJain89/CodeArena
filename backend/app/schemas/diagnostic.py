from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class DiagnosticQuestionItem(BaseModel):
    problem_id: int
    title: str
    description: str
    topic_id: int
    topic_name: str
    question_type: str = "MCQ"
    options: Optional[List[str]] = None

    model_config = ConfigDict(from_attributes=True)


class DiagnosticStartResponse(BaseModel):
    assessment_id: int
    status: str
    total_questions: int
    questions: List[DiagnosticQuestionItem]

    model_config = ConfigDict(from_attributes=True)


class AnswerSubmissionItem(BaseModel):
    problem_id: int
    selected_answer: Optional[str] = None


class DiagnosticSubmitRequest(BaseModel):
    answers: List[AnswerSubmissionItem]


class TopicResultItem(BaseModel):
    topic_id: int
    topic_name: str
    questions: int
    correct: int
    score: float


class DiagnosticResultResponse(BaseModel):
    assessment_id: int
    status: str
    total_questions: int
    answered_questions: int
    correct_answers: int
    score: float
    started_at: datetime
    completed_at: Optional[datetime] = None
    topic_results: List[TopicResultItem] = []
    questions: Optional[List[DiagnosticQuestionItem]] = None

    model_config = ConfigDict(from_attributes=True)
