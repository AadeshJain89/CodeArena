from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.schemas.analytics import DashboardResponse
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])
analytics_service = AnalyticsService()


@router.get(
    "/dashboard",
    response_model=DashboardResponse,
    summary="Get protected user analytics & dashboard data for the authenticated user",
)
async def get_user_dashboard(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns aggregated dashboard analytics for the authenticated user combining
    overview metrics, diagnostic results, topic skill profiles, submission statistics,
    personalized recommendations, and gamification state.
    """
    dashboard_data = await analytics_service.get_user_dashboard_data(db, user_id=current_user.id)
    return dashboard_data
