from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, Float, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.diagnostic_assessment import DiagnosticAssessment
    from app.models.problem import Problem


class DiagnosticResponse(Base):
    __tablename__ = "diagnostic_responses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    assessment_id: Mapped[int] = mapped_column(Integer, ForeignKey("diagnostic_assessments.id", ondelete="CASCADE"), nullable=False, index=True)
    problem_id: Mapped[int] = mapped_column(Integer, ForeignKey("problems.id", ondelete="CASCADE"), nullable=False, index=True)
    selected_answer: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    execution_time_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    assessment: Mapped["DiagnosticAssessment"] = relationship("DiagnosticAssessment", back_populates="responses")
    problem: Mapped["Problem"] = relationship("Problem")
