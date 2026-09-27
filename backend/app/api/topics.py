from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.db import get_db
from app.models.topic import Topic
from app.schemas.topic import TopicResponse

router = APIRouter()


@router.get("", response_model=List[TopicResponse])
async def list_topics(
    db: AsyncSession = Depends(get_db),
):
    """Retrieve all problem topics."""
    result = await db.execute(select(Topic).order_by(Topic.id))
    topics = result.scalars().all()
    return topics


@router.get("/{topic_id}", response_model=TopicResponse)
async def get_topic(
    topic_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve a single topic by ID."""
    result = await db.execute(select(Topic).where(Topic.id == topic_id))
    topic = result.scalar_one_or_none()
    if topic is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Topic with ID {topic_id} not found",
        )
    return topic
