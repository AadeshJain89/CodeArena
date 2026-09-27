from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from sqlalchemy import Integer, ForeignKey, DateTime, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.diagnostic_assessment import DiagnosticAssessment
    from app.models.problem import Problem


class DiagnosticAssessmentQuestion(Base):
    __tablename__ = "diagnostic_assessment_questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    assessment_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("diagnostic_assessments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    problem_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("problems.id", ondelete="CASCADE"), nullable=False, index=True
    )
    question_order: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("assessment_id", "problem_id", name="uq_assessment_problem"),
    )

    assessment: Mapped["DiagnosticAssessment"] = relationship(
        "DiagnosticAssessment", back_populates="assessment_questions"
    )
    problem: Mapped["Problem"] = relationship("Problem")
