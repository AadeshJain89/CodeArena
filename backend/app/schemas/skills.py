from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class SkillProfileResponse(BaseModel):
    skill_profile_id: int
    user_id: int
    topic_id: int
    topic_name: str
    skill_score: float
    skill_level: str
    confidence: float
    problems_solved: int
    total_points: int
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
