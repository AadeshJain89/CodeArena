import enum
from datetime import datetime, timezone
from typing import List, Optional, Any, TYPE_CHECKING
from sqlalchemy import String, Text, DateTime, Integer, Enum as SQLEnum, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.topic import Topic
    from app.models.test_case import TestCase


class ProblemDifficulty(str, enum.Enum):
    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"


class Problem(Base):
    __tablename__ = "problems"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), unique=True, index=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(200), unique=True, index=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    difficulty: Mapped[ProblemDifficulty] = mapped_column(
        SQLEnum(ProblemDifficulty, name="problem_difficulty_enum", native_enum=True),
        nullable=False,
        index=True,
    )
    constraints: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    input_format: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    output_format: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    examples: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    starter_code: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    solution_language_support: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    topics: Mapped[List["Topic"]] = relationship(
        "Topic",
        secondary="problem_topic",
        back_populates="problems",
    )
    test_cases: Mapped[List["TestCase"]] = relationship(
        "TestCase",
        back_populates="problem",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Problem(id={self.id}, title='{self.title}', difficulty='{self.difficulty}')>"
