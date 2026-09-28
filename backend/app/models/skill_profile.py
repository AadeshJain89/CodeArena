from datetime import datetime, timezone
from typing import TYPE_CHECKING
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.topic import Topic


class SkillProfile(Base):
    __tablename__ = "skill_profiles"

    skill_profile_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    topic_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("topics.id", ondelete="CASCADE"), nullable=False, index=True
    )
    skill_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    skill_level: Mapped[str] = mapped_column(String(50), default="BEGINNER", nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    problems_solved: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("user_id", "topic_id", name="uq_user_topic_skill"),
    )

    user: Mapped["User"] = relationship("User", back_populates="skill_profiles")
    topic: Mapped["Topic"] = relationship("Topic")

    def __repr__(self) -> str:
        return (
            f"<SkillProfile(id={self.skill_profile_id}, user_id={self.user_id}, "
            f"topic_id={self.topic_id}, level='{self.skill_level}', score={self.skill_score})>"
        )
