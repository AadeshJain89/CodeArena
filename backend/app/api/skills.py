from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.db import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.models.topic import Topic
from app.models.skill_profile import SkillProfile
from app.schemas.skills import SkillProfileResponse
from app.services.slre_service import (
    SLREService,
    DEFAULT_UNTESTED_SKILL,
    DEFAULT_UNTESTED_CONFIDENCE,
    compute_skill_level_name,
)

router = APIRouter(prefix="/skills", tags=["Skills"])
slre_service = SLREService()


@router.get(
    "",
    response_model=List[SkillProfileResponse],
    summary="Get authenticated user's skill profiles for all topics",
)
async def get_user_skill_profiles(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns the authenticated user's 12 topic skill profiles.
    If any topic profiles are missing, initializes default profiles for them.
    """
    # Fetch all 12 topics
    stmt_topics = select(Topic).order_by(Topic.id.asc())
    all_topics = (await db.execute(stmt_topics)).scalars().all()

    # Fetch user's existing skill profiles
    stmt_sp = (
        select(SkillProfile)
        .options(selectinload(SkillProfile.topic))
        .where(SkillProfile.user_id == current_user.id)
    )
    existing_sp_list = (await db.execute(stmt_sp)).scalars().all()
    sp_map = {sp.topic_id: sp for sp in existing_sp_list}

    results: List[SkillProfileResponse] = []
    need_commit = False

    for topic in all_topics:
        if topic.id in sp_map:
            sp = sp_map[topic.id]
        else:
            # Initialize default skill profile for missing topic
            sp = SkillProfile(
                user_id=current_user.id,
                topic_id=topic.id,
                skill_score=DEFAULT_UNTESTED_SKILL,
                skill_level=compute_skill_level_name(DEFAULT_UNTESTED_SKILL),
                confidence=DEFAULT_UNTESTED_CONFIDENCE,
                problems_solved=0,
                total_points=0,
            )
            sp.topic = topic
            db.add(sp)
            need_commit = True

        results.append(
            SkillProfileResponse(
                skill_profile_id=sp.skill_profile_id or 0,
                user_id=current_user.id,
                topic_id=topic.id,
                topic_name=sp.topic.name if sp.topic else topic.name,
                skill_score=sp.skill_score,
                skill_level=sp.skill_level,
                confidence=sp.confidence,
                problems_solved=sp.problems_solved,
                total_points=sp.total_points,
                updated_at=sp.updated_at,
            )
        )

    if need_commit:
        await db.commit()

    return results


@router.get(
    "/{topic_id}",
    response_model=SkillProfileResponse,
    summary="Get authenticated user's skill profile for a specific topic",
)
async def get_user_topic_skill_profile(
    topic_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns the authenticated user's skill profile for the specified topic.
    Users cannot access another user's skill profiles.
    """
    topic = await db.get(Topic, topic_id)
    if topic is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Topic with ID {topic_id} not found",
        )

    stmt_sp = (
        select(SkillProfile)
        .options(selectinload(SkillProfile.topic))
        .where(
            SkillProfile.user_id == current_user.id,
            SkillProfile.topic_id == topic_id,
        )
    )
    sp = (await db.execute(stmt_sp)).scalar_one_or_none()

    if sp is None:
        sp = SkillProfile(
            user_id=current_user.id,
            topic_id=topic_id,
            skill_score=DEFAULT_UNTESTED_SKILL,
            skill_level=compute_skill_level_name(DEFAULT_UNTESTED_SKILL),
            confidence=DEFAULT_UNTESTED_CONFIDENCE,
            problems_solved=0,
            total_points=0,
        )
        sp.topic = topic
        db.add(sp)
        await db.commit()
        await db.refresh(sp)

    return SkillProfileResponse(
        skill_profile_id=sp.skill_profile_id,
        user_id=current_user.id,
        topic_id=topic.id,
        topic_name=sp.topic.name if sp.topic else topic.name,
        skill_score=sp.skill_score,
        skill_level=sp.skill_level,
        confidence=sp.confidence,
        problems_solved=sp.problems_solved,
        total_points=sp.total_points,
        updated_at=sp.updated_at,
    )
