from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.schemas.recommendation import RecommendationResponse
from app.services.recommendation_service import RecommendationService

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])
recommendation_service = RecommendationService()


@router.get(
    "",
    response_model=List[RecommendationResponse],
    summary="Get authenticated user's top 5 personalized problem recommendations",
)
async def get_user_recommendations(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns the authenticated user's Top 5 personalized problem recommendations based on their
    current topic skill profiles, problem difficulty, topic relevance, and submission history.
    """
    recommendations = await recommendation_service.get_user_recommendations(db, user_id=current_user.id)

    # Map recommendations to response schema explicitly
    response_list = []
    for rec in recommendations:
        prob = rec.problem
        prob_difficulty = prob.difficulty.value if hasattr(prob.difficulty, 'value') else str(prob.difficulty)

        topics_summary = [
            {"id": t.id, "name": t.name}
            for t in (prob.topics or [])
        ]

        prob_summary = {
            "id": prob.id,
            "title": prob.title,
            "slug": prob.slug,
            "difficulty": prob_difficulty,
            "description": prob.description,
            "topics": topics_summary,
        }

        response_list.append({
            "recommendation_id": rec.recommendation_id,
            "user_id": rec.user_id,
            "problem_id": rec.problem_id,
            "rank": rec.rank,
            "score": rec.score,
            "reasons": rec.reasons,
            "generated_at": rec.generated_at,
            "problem": prob_summary,
        })

    return response_list