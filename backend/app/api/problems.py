import math
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, distinct
from sqlalchemy.orm import selectinload

from app.core.db import get_db
from app.models.problem import Problem, ProblemDifficulty
from app.models.topic import Topic
from app.schemas.problem import ProblemListItem, ProblemDetail, PaginatedProblemResponse
from app.schemas.test_case import TestCasePublic

router = APIRouter()


@router.get("", response_model=PaginatedProblemResponse)
async def list_problems(
    topic: Optional[str] = Query(None, description="Filter by topic name or topic ID"),
    difficulty: Optional[ProblemDifficulty] = Query(None, description="Filter by difficulty (EASY, MEDIUM, HARD)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve list of problems with optional topic/difficulty filtering and pagination."""
    # Build base query
    stmt = select(Problem).options(selectinload(Problem.topics))

    # Topic filtering
    if topic:
        topic_clean = topic.strip()
        if topic_clean.isdigit():
            topic_id = int(topic_clean)
            stmt = stmt.join(Problem.topics).where(Topic.id == topic_id)
        else:
            stmt = stmt.join(Problem.topics).where(Topic.name.ilike(topic_clean))

    # Difficulty filtering
    if difficulty:
        stmt = stmt.where(Problem.difficulty == difficulty)

    # Calculate total count for pagination
    # Use distinct(Problem.id) to handle joins correctly
    count_stmt = select(func.count(distinct(Problem.id)))
    if topic:
        topic_clean = topic.strip()
        if topic_clean.isdigit():
            count_stmt = count_stmt.select_from(Problem).join(Problem.topics).where(Topic.id == int(topic_clean))
        else:
            count_stmt = count_stmt.select_from(Problem).join(Problem.topics).where(Topic.name.ilike(topic_clean))
    else:
        count_stmt = count_stmt.select_from(Problem)

    if difficulty:
        count_stmt = count_stmt.where(Problem.difficulty == difficulty)

    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()

    # Apply order and pagination
    offset = (page - 1) * page_size
    stmt = stmt.order_by(Problem.id).offset(offset).limit(page_size)

    result = await db.execute(stmt)
    problems = result.scalars().all()

    total_pages = math.ceil(total / page_size) if total > 0 else 0

    return PaginatedProblemResponse(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        items=[ProblemListItem.model_validate(p) for p in problems],
    )


@router.get("/{problem_id}", response_model=ProblemDetail)
async def get_problem_detail(
    problem_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve detailed problem definition by ID. Excludes hidden test cases."""
    stmt = (
        select(Problem)
        .options(selectinload(Problem.topics), selectinload(Problem.test_cases))
        .where(Problem.id == problem_id)
    )
    result = await db.execute(stmt)
    problem = result.scalar_one_or_none()

    if problem is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Problem with ID {problem_id} not found",
        )

    # Filter out hidden test cases (Expose ONLY public test cases)
    public_cases = [
        TestCasePublic.model_validate(tc)
        for tc in problem.test_cases
        if not tc.is_hidden
    ]

    return ProblemDetail(
        id=problem.id,
        title=problem.title,
        slug=problem.slug,
        description=problem.description,
        difficulty=problem.difficulty,
        constraints=problem.constraints,
        input_format=problem.input_format,
        output_format=problem.output_format,
        examples=problem.examples,
        starter_code=problem.starter_code,
        solution_language_support=problem.solution_language_support,
        topics=[t for t in problem.topics],
        public_test_cases=public_cases,
        created_at=problem.created_at,
        updated_at=problem.updated_at,
    )
