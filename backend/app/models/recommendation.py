from datetime import datetime, timezone
from typing import List, Optional, Any, TYPE_CHECKING
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, UniqueConstraint, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.problem import Problem


class Recommendation(Base):
    __tablename__ = "recommendations"

    recommendation_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    problem_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("problems.id", ondelete="CASCADE"), nullable=False, index=True
    )
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    reasons: Mapped[Any] = mapped_column(JSON, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("user_id", "problem_id", name="uq_user_problem_recommendation"),
    )

    user: Mapped["User"] = relationship("User", back_populates="recommendations")
    problem: Mapped["Problem"] = relationship("Problem")

    def __repr__(self) -> str:
        return (
            f"<Recommendation(id={self.recommendation_id}, user_id={self.user_id}, "
            f"problem_id={self.problem_id}, rank={self.rank}, score={self.score})>"
        )
