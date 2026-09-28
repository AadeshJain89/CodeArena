from app.schemas.user import UserRegister, UserLogin, UserResponse, Token, TokenData
from app.schemas.topic import TopicResponse
from app.schemas.test_case import TestCasePublic, TestCaseCreate, TestCaseUpdate, TestCaseAdminResponse
from app.schemas.problem import ProblemListItem, ProblemDetail, PaginatedProblemResponse, ProblemCreate, ProblemUpdate, AdminProblemDetail
from app.schemas.execution import ExecutionRequest, ExecutionResponse, TestResultItem
from app.schemas.submission import (
    SubmissionCreate,
    SubmissionResponse,
    SubmissionSummaryResponse,
    SubmissionTestResultResponse,
)
from app.schemas.diagnostic import (
    DiagnosticQuestionItem,
    DiagnosticStartResponse,
    DiagnosticSubmitRequest,
    DiagnosticResultResponse,
    TopicResultItem,
)
from app.schemas.skills import SkillProfileResponse
from app.schemas.recommendation import RecommendationResponse
from app.schemas.gamification import UserGamificationResponse
from app.schemas.analytics import DashboardResponse

__all__ = [
    "UserRegister",
    "UserLogin",
    "UserResponse",
    "Token",
    "TokenData",
    "TopicResponse",
    "TestCasePublic",
    "TestCaseCreate",
    "TestCaseUpdate",
    "TestCaseAdminResponse",
    "ProblemListItem",
    "ProblemDetail",
    "PaginatedProblemResponse",
    "ProblemCreate",
    "ProblemUpdate",
    "AdminProblemDetail",
    "ExecutionRequest",
    "ExecutionResponse",
    "TestResultItem",
    "SubmissionCreate",
    "SubmissionResponse",
    "SubmissionSummaryResponse",
    "SubmissionTestResultResponse",
    "DiagnosticQuestionItem",
    "DiagnosticStartResponse",
    "DiagnosticSubmitRequest",
    "DiagnosticResultResponse",
    "TopicResultItem",
    "SkillProfileResponse",
    "RecommendationResponse",
    "UserGamificationResponse",
    "DashboardResponse",
]
