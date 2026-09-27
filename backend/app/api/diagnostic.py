from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.schemas.diagnostic import (
    DiagnosticStartResponse,
    DiagnosticSubmitRequest,
    DiagnosticResultResponse,
)
from app.services.diagnostic_service import DiagnosticService

router = APIRouter(prefix="/diagnostic", tags=["Diagnostic"])
diagnostic_service = DiagnosticService()


@router.post(
    "/start",
    response_model=DiagnosticStartResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start a new diagnostic assessment",
)
async def start_assessment(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new IN_PROGRESS diagnostic assessment for the user with approximately 10 MCQ questions.
    Correct answers are strictly masked.
    """
    return await diagnostic_service.start_assessment(
        db=db,
        user_id=current_user.id,
    )


@router.get(
    "/{assessment_id}",
    response_model=DiagnosticResultResponse,
    summary="Get assessment details by ID",
)
async def get_assessment(
    assessment_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve current status, questions, and responses for a diagnostic assessment owned by the user.
    Correct answers are strictly masked for active/uncompleted assessments.
    """
    return await diagnostic_service.get_assessment(
        db=db,
        user_id=current_user.id,
        assessment_id=assessment_id,
    )


@router.post(
    "/{assessment_id}/submit",
    response_model=DiagnosticResultResponse,
    summary="Submit answers for a diagnostic assessment",
)
async def submit_assessment(
    assessment_id: int,
    request: DiagnosticSubmitRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Evaluate submitted answers against server-side stored correct answers, compute score,
    persist diagnostic responses, mark assessment COMPLETED, and return topic-wise results.
    """
    return await diagnostic_service.submit_assessment(
        db=db,
        user_id=current_user.id,
        assessment_id=assessment_id,
        request=request,
    )
