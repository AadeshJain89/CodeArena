from datetime import datetime, timezone
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.diagnostic_response import DiagnosticResponse
    from app.models.diagnostic_assessment_question import DiagnosticAssessmentQuestion


class DiagnosticAssessment(Base):
    __tablename__ = "diagnostic_assessments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), default="IN_PROGRESS", nullable=False, index=True)
    total_questions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    answered_questions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    correct_answers: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    user: Mapped["User"] = relationship("User", back_populates="diagnostic_assessments")
    responses: Mapped[List["DiagnosticResponse"]] = relationship(
        "DiagnosticResponse",
        back_populates="assessment",
        cascade="all, delete-orphan",
        order_by="DiagnosticResponse.id",
    )
    assessment_questions: Mapped[List["DiagnosticAssessmentQuestion"]] = relationship(
        "DiagnosticAssessmentQuestion",
        back_populates="assessment",
        cascade="all, delete-orphan",
        order_by="DiagnosticAssessmentQuestion.question_order.asc()",
    )
