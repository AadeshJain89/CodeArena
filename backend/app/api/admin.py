import math
import re
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, distinct, delete
from sqlalchemy.orm import selectinload

from app.core.db import get_db
from app.api.deps import require_role
from app.models.user import User, UserRole
from app.models.problem import Problem, ProblemDifficulty
from app.models.topic import Topic
from app.models.problem_topic import ProblemTopic
from app.models.test_case import TestCase
from app.models.submission import Submission
from app.models.diagnostic_response import DiagnosticResponse
from app.models.diagnostic_assessment_question import DiagnosticAssessmentQuestion
from app.models.recommendation import Recommendation
from app.schemas.problem import (
    ProblemListItem,
    ProblemCreate,
    ProblemUpdate,
    AdminProblemDetail,
    PaginatedProblemResponse,
)
from app.schemas.test_case import (
    TestCaseCreate,
    TestCaseUpdate,
    TestCaseAdminResponse,
)

router = APIRouter(dependencies=[Depends(require_role(UserRole.ADMIN))])


@router.get("/test", summary="Test admin authorization")
async def admin_test(
    admin_user: User = Depends(require_role(UserRole.ADMIN)),
):
    """Protected admin endpoint test."""
    return {
        "message": "Admin authorization verified successfully",
        "username": admin_user.username,
        "email": admin_user.email,
        "role": admin_user.role.value,
    }


# ==================================================
# PROBLEM MANAGEMENT ENDPOINTS
# ==================================================

@router.post(
    "/problems",
    response_model=AdminProblemDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new problem (Admin only)",
)
async def create_problem(
    req: ProblemCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new problem, associate topics, and initialize problem metadata."""
    # Generate slug if not provided
    slug = req.slug.strip() if req.slug else re.sub(r"[^a-z0-9]+", "-", req.title.lower()).strip("-")

    # Check title uniqueness
    stmt_title = select(Problem).where(Problem.title == req.title.strip())
    existing_title = (await db.execute(stmt_title)).scalar_one_or_none()
    if existing_title:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Problem with title '{req.title}' already exists",
        )

    # Check slug uniqueness
    stmt_slug = select(Problem).where(Problem.slug == slug)
    existing_slug = (await db.execute(stmt_slug)).scalar_one_or_none()
    if existing_slug:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Problem with slug '{slug}' already exists",
        )

    # Validate topic_ids if provided
    topic_ids = list(set(req.topic_ids)) if req.topic_ids else []
    if topic_ids:
        stmt_topics = select(Topic).where(Topic.id.in_(topic_ids))
        found_topics = (await db.execute(stmt_topics)).scalars().all()
        if len(found_topics) != len(topic_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="One or more specified topic_ids do not exist",
            )

    # Create problem
    problem = Problem(
        title=req.title.strip(),
        slug=slug,
        description=req.description,
        difficulty=req.difficulty,
        constraints=req.constraints,
        input_format=req.input_format,
        output_format=req.output_format,
        examples=req.examples,
        starter_code=req.starter_code,
        solution_language_support=req.solution_language_support,
        is_diagnostic=req.is_diagnostic,
        diagnostic_options=req.diagnostic_options,
        diagnostic_correct_option=req.diagnostic_correct_option,
        question_type=req.question_type or "CODING",
        options=req.options,
        correct_option=req.correct_option,
    )
    db.add(problem)
    await db.flush()

    # Create ProblemTopic relationships
    for tid in topic_ids:
        pt = ProblemTopic(problem_id=problem.id, topic_id=tid)
        db.add(pt)

    await db.commit()

    # Re-fetch problem with relationships
    stmt_full = (
        select(Problem)
        .options(selectinload(Problem.topics), selectinload(Problem.test_cases))
        .where(Problem.id == problem.id)
    )
    problem_full = (await db.execute(stmt_full)).scalar_one()

    return AdminProblemDetail(
        id=problem_full.id,
        title=problem_full.title,
        slug=problem_full.slug,
        description=problem_full.description,
        difficulty=problem_full.difficulty,
        constraints=problem_full.constraints,
        input_format=problem_full.input_format,
        output_format=problem_full.output_format,
        examples=problem_full.examples,
        starter_code=problem_full.starter_code,
        solution_language_support=problem_full.solution_language_support,
        is_diagnostic=problem_full.is_diagnostic,
        diagnostic_options=problem_full.diagnostic_options,
        diagnostic_correct_option=problem_full.diagnostic_correct_option,
        question_type=problem_full.question_type,
        options=problem_full.options,
        correct_option=problem_full.correct_option,
        topics=[t for t in problem_full.topics],
        test_cases=[tc for tc in problem_full.test_cases],
        created_at=problem_full.created_at,
        updated_at=problem_full.updated_at,
    )


@router.get(
    "/problems",
    response_model=PaginatedProblemResponse,
    summary="List problems for admin management",
)
async def list_admin_problems(
    topic_id: Optional[int] = Query(None, description="Filter by topic ID"),
    difficulty: Optional[ProblemDifficulty] = Query(None, description="Filter by difficulty"),
    search: Optional[str] = Query(None, description="Search term for title/slug"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
):
    """List problems with optional topic, difficulty, or search filtering."""
    stmt = select(Problem).options(selectinload(Problem.topics))

    if topic_id is not None:
        stmt = stmt.join(Problem.topics).where(Topic.id == topic_id)

    if difficulty:
        stmt = stmt.where(Problem.difficulty == difficulty)

    if search and search.strip():
        term = f"%{search.strip()}%"
        stmt = stmt.where(Problem.title.ilike(term) | Problem.slug.ilike(term))

    # Calculate count
    count_stmt = select(func.count(distinct(Problem.id)))
    if topic_id is not None:
        count_stmt = count_stmt.select_from(Problem).join(Problem.topics).where(Topic.id == topic_id)
    else:
        count_stmt = count_stmt.select_from(Problem)

    if difficulty:
        count_stmt = count_stmt.where(Problem.difficulty == difficulty)

    if search and search.strip():
        term = f"%{search.strip()}%"
        count_stmt = count_stmt.where(Problem.title.ilike(term) | Problem.slug.ilike(term))

    total = (await db.execute(count_stmt)).scalar_one()

    # Pagination
    offset = (page - 1) * page_size
    stmt = stmt.order_by(Problem.id.asc()).offset(offset).limit(page_size)

    problems = (await db.execute(stmt)).scalars().all()
    total_pages = math.ceil(total / page_size) if total > 0 else 0

    return PaginatedProblemResponse(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        items=[ProblemListItem.model_validate(p) for p in problems],
    )


@router.get(
    "/problems/{problem_id}",
    response_model=AdminProblemDetail,
    summary="Get complete admin problem details including all test cases",
)
async def get_admin_problem_detail(
    problem_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve complete problem info including topic associations and all test cases."""
    stmt = (
        select(Problem)
        .options(selectinload(Problem.topics), selectinload(Problem.test_cases))
        .where(Problem.id == problem_id)
    )
    problem = (await db.execute(stmt)).scalar_one_or_none()

    if problem is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Problem with ID {problem_id} not found",
        )

    return AdminProblemDetail(
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
        is_diagnostic=problem.is_diagnostic,
        diagnostic_options=problem.diagnostic_options,
        diagnostic_correct_option=problem.diagnostic_correct_option,
        question_type=problem.question_type,
        options=problem.options,
        correct_option=problem.correct_option,
        topics=[t for t in problem.topics],
        test_cases=[tc for tc in problem.test_cases],
        created_at=problem.created_at,
        updated_at=problem.updated_at,
    )


@router.put(
    "/problems/{problem_id}",
    response_model=AdminProblemDetail,
    summary="Update an existing problem (Admin only)",
)
async def update_problem(
    problem_id: int,
    req: ProblemUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update an existing problem and synchronize topic associations."""
    stmt = (
        select(Problem)
        .options(selectinload(Problem.topics), selectinload(Problem.test_cases))
        .where(Problem.id == problem_id)
    )
    problem = (await db.execute(stmt)).scalar_one_or_none()

    if problem is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Problem with ID {problem_id} not found",
        )

    # Title & Slug updates
    if req.title is not None and req.title.strip() != problem.title:
        new_title = req.title.strip()
        new_slug = (
            req.slug.strip()
            if req.slug and req.slug.strip()
            else re.sub(r"[^a-z0-9]+", "-", new_title.lower()).strip("-")
        )

        # Uniqueness checks
        stmt_t = select(Problem).where(Problem.title == new_title, Problem.id != problem_id)
        if (await db.execute(stmt_t)).scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Problem title '{new_title}' already in use by another problem",
            )

        stmt_s = select(Problem).where(Problem.slug == new_slug, Problem.id != problem_id)
        if (await db.execute(stmt_s)).scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Problem slug '{new_slug}' already in use by another problem",
            )

        problem.title = new_title
        problem.slug = new_slug
    elif req.slug is not None and req.slug.strip() != problem.slug:
        new_slug = req.slug.strip()
        stmt_s = select(Problem).where(Problem.slug == new_slug, Problem.id != problem_id)
        if (await db.execute(stmt_s)).scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Problem slug '{new_slug}' already in use by another problem",
            )
        problem.slug = new_slug

    # Update scalar attributes if provided
    if req.description is not None:
        problem.description = req.description
    if req.difficulty is not None:
        problem.difficulty = req.difficulty
    if req.constraints is not None:
        problem.constraints = req.constraints
    if req.input_format is not None:
        problem.input_format = req.input_format
    if req.output_format is not None:
        problem.output_format = req.output_format
    if req.examples is not None:
        problem.examples = req.examples
    if req.starter_code is not None:
        problem.starter_code = req.starter_code
    if req.solution_language_support is not None:
        problem.solution_language_support = req.solution_language_support
    if req.is_diagnostic is not None:
        problem.is_diagnostic = req.is_diagnostic
    if req.diagnostic_options is not None:
        problem.diagnostic_options = req.diagnostic_options
    if req.diagnostic_correct_option is not None:
        problem.diagnostic_correct_option = req.diagnostic_correct_option
    if req.question_type is not None:
        problem.question_type = req.question_type
    if req.options is not None:
        problem.options = req.options
    if req.correct_option is not None:
        problem.correct_option = req.correct_option

    # Synchronize topic_ids if supplied
    if req.topic_ids is not None:
        target_tids = list(set(req.topic_ids))
        found_topics = []
        if target_tids:
            stmt_topics = select(Topic).where(Topic.id.in_(target_tids))
            found_topics = (await db.execute(stmt_topics)).scalars().all()
            if len(found_topics) != len(target_tids):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="One or more specified topic_ids do not exist",
                )
        problem.topics = list(found_topics)

    problem.updated_at = datetime.now(timezone.utc)
    await db.commit()

    # Re-fetch problem with relationships
    stmt_full = (
        select(Problem)
        .options(selectinload(Problem.topics), selectinload(Problem.test_cases))
        .where(Problem.id == problem_id)
    )
    problem_full = (await db.execute(stmt_full)).scalar_one()

    return AdminProblemDetail(
        id=problem_full.id,
        title=problem_full.title,
        slug=problem_full.slug,
        description=problem_full.description,
        difficulty=problem_full.difficulty,
        constraints=problem_full.constraints,
        input_format=problem_full.input_format,
        output_format=problem_full.output_format,
        examples=problem_full.examples,
        starter_code=problem_full.starter_code,
        solution_language_support=problem_full.solution_language_support,
        is_diagnostic=problem_full.is_diagnostic,
        diagnostic_options=problem_full.diagnostic_options,
        diagnostic_correct_option=problem_full.diagnostic_correct_option,
        question_type=problem_full.question_type,
        options=problem_full.options,
        correct_option=problem_full.correct_option,
        topics=[t for t in problem_full.topics],
        test_cases=[tc for tc in problem_full.test_cases],
        created_at=problem_full.created_at,
        updated_at=problem_full.updated_at,
    )


@router.delete(
    "/problems/{problem_id}",
    summary="Delete a problem (Admin only)",
)
async def delete_problem(
    problem_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a problem only if it has NO historical/domain records.

    Checks the following FK references before allowing deletion:
      - Submission (user submission history)
      - DiagnosticResponse (user diagnostic answers referencing this problem)
      - DiagnosticAssessmentQuestion (diagnostic assessment question references)
      - Recommendation (personalized recommendation records)

    If any of these exist, returns HTTP 409 Conflict to preserve historical data.
    Safe child records (ProblemTopic, TestCase) are cleaned up by cascade on deletion.
    """
    stmt = select(Problem).where(Problem.id == problem_id)
    problem = (await db.execute(stmt)).scalar_one_or_none()

    if problem is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Problem with ID {problem_id} not found",
        )

    # --- Check for historical dependencies that must NOT be silently deleted ---

    # 1. Submissions: user code submission records
    sub_count = (
        await db.execute(
            select(func.count(Submission.id)).where(Submission.problem_id == problem_id)
        )
    ).scalar_one()
    if sub_count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Cannot delete problem #{problem_id}: it has {sub_count} submission(s). "
                "Deleting this problem would destroy historical user submission data. "
                "Remove or reassign submissions before deleting the problem."
            ),
        )

    # 2. DiagnosticResponses: user diagnostic answer records referencing this problem
    diag_resp_count = (
        await db.execute(
            select(func.count(DiagnosticResponse.id)).where(
                DiagnosticResponse.problem_id == problem_id
            )
        )
    ).scalar_one()
    if diag_resp_count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Cannot delete problem #{problem_id}: it has {diag_resp_count} diagnostic response(s). "
                "Deleting this problem would destroy historical diagnostic session data."
            ),
        )

    # 3. DiagnosticAssessmentQuestions: questions in active diagnostic assessments
    diag_q_count = (
        await db.execute(
            select(func.count(DiagnosticAssessmentQuestion.id)).where(
                DiagnosticAssessmentQuestion.problem_id == problem_id
            )
        )
    ).scalar_one()
    if diag_q_count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Cannot delete problem #{problem_id}: it is referenced by {diag_q_count} "
                "diagnostic assessment question(s). Remove those assessment references first."
            ),
        )

    # 4. Recommendations: personalized recommendation records
    rec_count = (
        await db.execute(
            select(func.count(Recommendation.recommendation_id)).where(
                Recommendation.problem_id == problem_id
            )
        )
    ).scalar_one()
    if rec_count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Cannot delete problem #{problem_id}: it has {rec_count} recommendation record(s). "
                "Deleting this problem would destroy user recommendation history."
            ),
        )

    # No historical dependencies — safe to delete.
    # ProblemTopic and TestCase rows will cascade-delete via DB FK ON DELETE CASCADE.
    await db.delete(problem)
    await db.commit()

    return {"message": f"Problem #{problem_id} deleted successfully"}


# ==================================================
# TEST CASE MANAGEMENT ENDPOINTS
# ==================================================

@router.post(
    "/problems/{problem_id}/test-cases",
    response_model=TestCaseAdminResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a test case for a problem (Admin only)",
)
async def create_test_case(
    problem_id: int,
    req: TestCaseCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new public or hidden test case for a problem."""
    stmt_p = select(Problem).where(Problem.id == problem_id)
    problem = (await db.execute(stmt_p)).scalar_one_or_none()
    if problem is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Problem with ID {problem_id} not found",
        )

    tc = TestCase(
        problem_id=problem_id,
        input=req.input,
        expected_output=req.expected_output,
        is_hidden=req.is_hidden,
        time_limit_override=req.time_limit_override,
        memory_limit_override=req.memory_limit_override,
    )
    db.add(tc)
    await db.commit()
    await db.refresh(tc)

    return tc


@router.get(
    "/problems/{problem_id}/test-cases",
    response_model=List[TestCaseAdminResponse],
    summary="List all test cases for a problem (Admin only)",
)
async def list_problem_test_cases(
    problem_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve all test cases (both public and hidden) for a specific problem."""
    stmt_p = select(Problem).where(Problem.id == problem_id)
    problem = (await db.execute(stmt_p)).scalar_one_or_none()
    if problem is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Problem with ID {problem_id} not found",
        )

    stmt_tc = (
        select(TestCase)
        .where(TestCase.problem_id == problem_id)
        .order_by(TestCase.test_case_id.asc())
    )
    test_cases = (await db.execute(stmt_tc)).scalars().all()
    return test_cases


@router.get(
    "/test-cases/{test_case_id}",
    response_model=TestCaseAdminResponse,
    summary="Get single test case detail (Admin only)",
)
async def get_test_case_detail(
    test_case_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve test case details by test_case_id."""
    stmt = select(TestCase).where(TestCase.test_case_id == test_case_id)
    tc = (await db.execute(stmt)).scalar_one_or_none()
    if tc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test case with ID {test_case_id} not found",
        )
    return tc


@router.put(
    "/test-cases/{test_case_id}",
    response_model=TestCaseAdminResponse,
    summary="Update a test case (Admin only)",
)
async def update_test_case(
    test_case_id: int,
    req: TestCaseUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update test case properties."""
    stmt = select(TestCase).where(TestCase.test_case_id == test_case_id)
    tc = (await db.execute(stmt)).scalar_one_or_none()
    if tc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test case with ID {test_case_id} not found",
        )

    if req.input is not None:
        tc.input = req.input
    if req.expected_output is not None:
        tc.expected_output = req.expected_output
    if req.is_hidden is not None:
        tc.is_hidden = req.is_hidden
    if req.time_limit_override is not None:
        tc.time_limit_override = req.time_limit_override
    if req.memory_limit_override is not None:
        tc.memory_limit_override = req.memory_limit_override

    await db.commit()
    await db.refresh(tc)
    return tc


@router.delete(
    "/test-cases/{test_case_id}",
    summary="Delete a test case (Admin only)",
)
async def delete_test_case(
    test_case_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Delete a test case by test_case_id."""
    stmt = select(TestCase).where(TestCase.test_case_id == test_case_id)
    tc = (await db.execute(stmt)).scalar_one_or_none()
    if tc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test case with ID {test_case_id} not found",
        )

    await db.delete(tc)
    await db.commit()
    return {"message": f"Test case #{test_case_id} deleted successfully"}
