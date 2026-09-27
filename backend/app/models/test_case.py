from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from sqlalchemy import Text, Boolean, Float, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.problem import Problem


class TestCase(Base):
    __tablename__ = "test_cases"

    test_case_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    problem_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("problems.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    input: Mapped[str] = mapped_column(Text, nullable=False)
    expected_output: Mapped[str] = mapped_column(Text, nullable=False)
    is_hidden: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    time_limit_override: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    memory_limit_override: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    problem: Mapped["Problem"] = relationship("Problem", back_populates="test_cases")

    def __repr__(self) -> str:
        return f"<TestCase(id={self.test_case_id}, problem_id={self.problem_id}, is_hidden={self.is_hidden})>"
