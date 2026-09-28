import uuid
from datetime import datetime, timezone
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool

from app.main import app
from app.core.config import settings
from app.core.db import get_db
from app.core.security import create_access_token, hash_password
from app.models.user import User, UserRole
from app.models.problem import Problem, ProblemDifficulty
from app.models.submission import Submission
from app.models.diagnostic_assessment import DiagnosticAssessment
from app.models.skill_profile import SkillProfile
from app.seed_data import seed_data
from app.services.gamification_service import GamificationService


test_engine = create_async_engine(settings.ASYNC_DATABASE_URI, poolclass=NullPool, echo=False)
TestSessionLocal = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db():
    async with TestSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture(autouse=True, scope="function")
async def ensure_seeded_db():
    async with TestSessionLocal() as session:
        await seed_data(session=session)


async def create_test_user(prefix: str = "analytics_user") -> int:
    unique_str = uuid.uuid4().hex[:8]
    async with TestSessionLocal() as session:
        u = User(
            username=f"{prefix}_{unique_str}",
            email=f"{prefix}_{unique_str}@example.com",
            password_hash=hash_password("Password123!"),
            role=UserRole.USER,
            is_active=True,
        )
        session.add(u)
        await session.commit()
        await session.refresh(u)
        return u.id


def get_auth_header(user_id: int, role: str = "USER"):
    token = create_access_token(subject=str(user_id), role=role)
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_1_authenticated_dashboard_access():
    user_id = await create_test_user("test1")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/analytics/dashboard", headers=get_auth_header(user_id))
    assert response.status_code == 200
    data = response.json()
    assert "overview" in data
    assert "diagnostic" in data
    assert "skills" in data
    assert "submissions" in data
    assert "recommendations" in data
    assert "gamification" in data


@pytest.mark.asyncio
async def test_2_unauthenticated_access_rejected():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/analytics/dashboard")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_3_brand_new_user_gets_safe_empty_dashboard():
    user_id = await create_test_user("brand_new")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/analytics/dashboard", headers=get_auth_header(user_id))
    assert response.status_code == 200
    data = response.json()

    assert data["overview"]["total_submissions"] == 0
    assert data["overview"]["total_problems_solved"] == 0
    assert data["overview"]["success_rate"] == 0.0
    assert data["diagnostic"]["has_completed_diagnostic"] is False
    assert len(data["skills"]) == 12  # All 12 topics represented with default values
    assert data["submissions"]["total_submissions"] == 0
    assert data["submissions"]["recent_submissions"] == []


@pytest.mark.asyncio
async def test_4_overview_statistics_correct():
    user_id = await create_test_user("test4")
    async with TestSessionLocal() as db:
        probs = (await db.execute(select(Problem))).scalars().all()
        # 1 Passed, 1 Failed
        sub1 = Submission(
            user_id=user_id,
            problem_id=probs[0].id,
            language="PYTHON",
            source_code="pass",
            status="PASSED",
            total_tests=1,
            passed_tests=1,
            failed_tests=0,
            execution_time_ms=12.5,
            created_at=datetime.now(timezone.utc),
        )
        sub2 = Submission(
            user_id=user_id,
            problem_id=probs[1].id,
            language="PYTHON",
            source_code="fail",
            status="FAILED",
            total_tests=1,
            passed_tests=0,
            failed_tests=1,
            execution_time_ms=15.0,
            created_at=datetime.now(timezone.utc),
        )
        db.add_all([sub1, sub2])
        await db.commit()

        # Update gamification for passed solve
        gamification_service = GamificationService()
        await gamification_service.process_submission_for_gamification(db, sub1)
        await db.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/analytics/dashboard", headers=get_auth_header(user_id))

    assert response.status_code == 200
    overview = response.json()["overview"]
    assert overview["total_submissions"] == 2
    assert overview["successful_submissions"] == 1
    assert overview["failed_submissions"] == 1
    assert overview["success_rate"] == 50.0
    assert overview["total_problems_attempted"] == 2
    assert overview["total_problems_solved"] == 1


@pytest.mark.asyncio
async def test_5_submission_statistics_correct():
    user_id = await create_test_user("test5")
    async with TestSessionLocal() as db:
        prob = (await db.execute(select(Problem))).scalars().first()
        for s_status in ["PASSED", "PASSED", "FAILED"]:
            sub = Submission(
                user_id=user_id,
                problem_id=prob.id,
                language="PYTHON",
                source_code="code",
                status=s_status,
                total_tests=1,
                passed_tests=1 if s_status == "PASSED" else 0,
                failed_tests=0 if s_status == "PASSED" else 1,
                created_at=datetime.now(timezone.utc),
            )
            db.add(sub)
        await db.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/analytics/dashboard", headers=get_auth_header(user_id))

    subs_data = response.json()["submissions"]
    assert subs_data["total_submissions"] == 3
    assert subs_data["passed_submissions"] == 2
    assert subs_data["failed_submissions"] == 1


@pytest.mark.asyncio
async def test_6_success_rate_is_correct():
    user_id = await create_test_user("test6")
    async with TestSessionLocal() as db:
        prob = (await db.execute(select(Problem))).scalars().first()
        for s_status in ["PASSED", "FAILED", "FAILED", "FAILED"]:
            sub = Submission(
                user_id=user_id,
                problem_id=prob.id,
                language="PYTHON",
                source_code="code",
                status=s_status,
                total_tests=1,
                passed_tests=1 if s_status == "PASSED" else 0,
                failed_tests=0 if s_status == "PASSED" else 1,
                created_at=datetime.now(timezone.utc),
            )
            db.add(sub)
        await db.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/analytics/dashboard", headers=get_auth_header(user_id))

    data = response.json()
    assert data["overview"]["success_rate"] == 25.0
    assert data["submissions"]["success_rate"] == 25.0


@pytest.mark.asyncio
async def test_7_diagnostic_summary_appears():
    user_id = await create_test_user("test7")
    async with TestSessionLocal() as db:
        diag = DiagnosticAssessment(
            user_id=user_id,
            status="COMPLETED",
            total_questions=10,
            answered_questions=10,
            correct_answers=8,
            score=80.0,
            completed_at=datetime.now(timezone.utc),
        )
        db.add(diag)
        await db.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/analytics/dashboard", headers=get_auth_header(user_id))

    diag_data = response.json()["diagnostic"]
    assert diag_data["has_completed_diagnostic"] is True
    assert diag_data["score"] == 80.0
    assert diag_data["total_questions"] == 10
    assert diag_data["correct_answers"] == 8


@pytest.mark.asyncio
async def test_8_topic_skill_profiles_appear():
    user_id = await create_test_user("test8")
    async with TestSessionLocal() as db:
        sp = SkillProfile(
            user_id=user_id,
            topic_id=1,
            skill_score=65.5,
            skill_level="INTERMEDIATE",
            confidence=0.75,
            problems_solved=3,
            total_points=75,
        )
        db.add(sp)
        await db.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/analytics/dashboard", headers=get_auth_header(user_id))

    skills_data = response.json()["skills"]
    topic1_skill = next(s for s in skills_data if s["topic_id"] == 1)
    assert topic1_skill["skill_score"] == 65.5
    assert topic1_skill["skill_level"] == "INTERMEDIATE"
    assert topic1_skill["confidence"] == 0.75
    assert topic1_skill["problems_solved"] == 3


@pytest.mark.asyncio
async def test_9_topics_without_skill_profiles_handled_safely():
    user_id = await create_test_user("test9")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/analytics/dashboard", headers=get_auth_header(user_id))

    skills_data = response.json()["skills"]
    assert len(skills_data) == 12
    for s in skills_data:
        assert s["skill_score"] == 0.0
        assert s["skill_level"] == "NOVICE"
        assert s["confidence"] == 0.0


@pytest.mark.asyncio
async def test_10_recent_submissions_returned():
    user_id = await create_test_user("test10")
    async with TestSessionLocal() as db:
        probs = (await db.execute(select(Problem))).scalars().all()
        for i in range(12):
            sub = Submission(
                user_id=user_id,
                problem_id=probs[i % len(probs)].id,
                language="PYTHON",
                source_code=f"print({i})",
                status="PASSED",
                total_tests=1,
                passed_tests=1,
                failed_tests=0,
                execution_time_ms=10.0 + i,
                created_at=datetime.now(timezone.utc),
            )
            db.add(sub)
        await db.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/analytics/dashboard", headers=get_auth_header(user_id))

    rec_subs = response.json()["submissions"]["recent_submissions"]
    assert len(rec_subs) == 10  # Bounded to top 10 recent
    assert rec_subs[0]["problem_title"] is not None


@pytest.mark.asyncio
async def test_11_recommendations_included():
    user_id = await create_test_user("test11")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/analytics/dashboard", headers=get_auth_header(user_id))

    rec_data = response.json()["recommendations"]
    assert rec_data["total_recommendations"] <= 5
    if rec_data["total_recommendations"] > 0:
        rec1 = rec_data["recommendations"][0]
        assert "problem_title" in rec1
        assert "rank" in rec1
        assert "score" in rec1


@pytest.mark.asyncio
async def test_12_gamification_data_included():
    user_id = await create_test_user("test12")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/analytics/dashboard", headers=get_auth_header(user_id))

    gamification_data = response.json()["gamification"]
    assert "xp" in gamification_data
    assert "level" in gamification_data
    assert "xp_for_next_level" in gamification_data
    assert "badges" in gamification_data


@pytest.mark.asyncio
async def test_13_dashboard_only_returns_current_user_data():
    user1_id = await create_test_user("user_a")
    user2_id = await create_test_user("user_b")

    # User 1 submits 1 passed submission
    async with TestSessionLocal() as db:
        prob = (await db.execute(select(Problem))).scalars().first()
        sub = Submission(
            user_id=user1_id,
            problem_id=prob.id,
            language="PYTHON",
            source_code="solve",
            status="PASSED",
            total_tests=1,
            passed_tests=1,
            failed_tests=0,
            created_at=datetime.now(timezone.utc),
        )
        db.add(sub)
        await db.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res1 = await ac.get("/api/v1/analytics/dashboard", headers=get_auth_header(user1_id))
        res2 = await ac.get("/api/v1/analytics/dashboard", headers=get_auth_header(user2_id))

    data1 = res1.json()
    data2 = res2.json()

    assert data1["overview"]["total_submissions"] == 1
    assert data2["overview"]["total_submissions"] == 0


@pytest.mark.asyncio
async def test_14_mixed_submission_statuses_handled():
    user_id = await create_test_user("test14")
    statuses = ["PASSED", "FAILED", "TIME_LIMIT_EXCEEDED", "RUNTIME_ERROR"]
    async with TestSessionLocal() as db:
        prob = (await db.execute(select(Problem))).scalars().first()
        for s in statuses:
            sub = Submission(
                user_id=user_id,
                problem_id=prob.id,
                language="PYTHON",
                source_code="test",
                status=s,
                total_tests=1,
                passed_tests=1 if s == "PASSED" else 0,
                failed_tests=0 if s == "PASSED" else 1,
                created_at=datetime.now(timezone.utc),
            )
            db.add(sub)
        await db.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/analytics/dashboard", headers=get_auth_header(user_id))

    overview = response.json()["overview"]
    assert overview["total_submissions"] == 4
    assert overview["successful_submissions"] == 1
    assert overview["failed_submissions"] == 3
    assert overview["success_rate"] == 25.0


@pytest.mark.asyncio
async def test_15_no_submission_case_works():
    user_id = await create_test_user("no_sub")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/analytics/dashboard", headers=get_auth_header(user_id))

    assert response.status_code == 200
    subs_data = response.json()["submissions"]
    assert subs_data["total_submissions"] == 0
    assert subs_data["passed_submissions"] == 0
    assert subs_data["failed_submissions"] == 0
    assert subs_data["success_rate"] == 0.0
    assert subs_data["recent_submissions"] == []


@pytest.mark.asyncio
async def test_16_no_diagnostic_case_works():
    user_id = await create_test_user("no_diag")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/analytics/dashboard", headers=get_auth_header(user_id))

    assert response.status_code == 200
    diag_data = response.json()["diagnostic"]
    assert diag_data["has_completed_diagnostic"] is False
    assert diag_data["score"] is None
    assert diag_data["total_questions"] is None
    assert diag_data["correct_answers"] is None
    assert diag_data["percentage"] is None
    assert diag_data["completed_at"] is None
