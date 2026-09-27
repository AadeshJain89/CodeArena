from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.models.user import User
from app.api.deps import get_current_active_user
from app.schemas.execution import ExecutionRequest, ExecutionResponse
from app.services.execution_service import ExecutionService

router = APIRouter()
_execution_service = ExecutionService()


@router.post("", response_model=ExecutionResponse, status_code=status.HTTP_200_OK)
async def execute_code(
    request: ExecutionRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Execute submitted code in an isolated Docker container against problem test cases."""
    return await _execution_service.execute_code(request, db)
