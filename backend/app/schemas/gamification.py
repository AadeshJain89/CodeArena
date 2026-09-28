from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class UserGamificationResponse(BaseModel):
    gamification_id: int
    user_id: int
    xp: int
    level: int
    problems_solved: int
    successful_submissions: int
    current_streak: int
    longest_streak: int
    last_activity_date: Optional[date] = None
    badges: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
