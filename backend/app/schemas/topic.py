from datetime import datetime
from pydantic import BaseModel, ConfigDict


class TopicResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
