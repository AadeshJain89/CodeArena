from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.schemas.submission import (
    SubmissionCreate,
    SubmissionResponse,
    SubmissionSummaryResponse,
)
from app.services.submission_service import SubmissionService

router = APIRouter(prefix="/submissions", tags=["Submissions"])
submission_service = SubmissionService()


@router.post(
    "",
    response_model=SubmissionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit code solution for evaluation & persistence",
)
async def create_submission(
    request: SubmissionCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Evaluate submitted code against problem test cases, persist Submission & SubmissionTestResult records,
    and return evaluation results.
    """
    return await submission_service.create_submission(
        db=db,
        user_id=current_user.id,
        request=request,
    )


@router.get(
    "",
    response_model=List[SubmissionSummaryResponse],
    summary="Get submission history for current authenticated user",
)
async def get_user_submissions(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve list of submissions submitted by the current authenticated user (newest first)."""
    return await submission_service.get_user_submissions(
        db=db,
        user_id=current_user.id,
    )


@router.get(
    "/{submission_id}",
    response_model=SubmissionResponse,
    summary="Get details of a specific submission",
)
async def get_submission_detail(
    submission_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve detailed evaluation results for a specific submission owned by the current user."""
    return await submission_service.get_user_submission_detail(
        db=db,
        user_id=current_user.id,
        submission_id=submission_id,
    )
