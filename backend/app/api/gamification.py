from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.schemas.gamification import UserGamificationResponse
from app.services.gamification_service import GamificationService

router = APIRouter(prefix="/gamification", tags=["Gamification"])
gamification_service = GamificationService()


@router.get(
    "",
    response_model=UserGamificationResponse,
    summary="Get authenticated user's gamification statistics",
)
async def get_user_gamification(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns the authenticated user's current gamification data.
    Safely initializes a new gamification record if one does not exist yet.
    """
    gamification = await gamification_service.get_or_create_user_gamification(db, user_id=current_user.id)
    await db.commit()
    return gamification
