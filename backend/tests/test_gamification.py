import uuid
from datetime import datetime, timezone, timedelta, date
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
from app.models.user_gamification import UserGamification
from app.seed_data import seed_data
from app.services.gamification_service import GamificationService
from app.services.submission_service import SubmissionService
from unittest.mock import AsyncMock
from app.schemas.submission import SubmissionCreate
from app.schemas.execution import ExecutionResponse, TestResultItem


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


async def create_test_user(prefix: str = "gamification_user") -> int:
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
async def test_01_authenticated_gamification_endpoint():
    user_id = await create_test_user("test1")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/gamification", headers=get_auth_header(user_id))
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == user_id
    assert "xp" in data
    assert "level" in data
    assert "problems_solved" in data


@pytest.mark.asyncio
async def test_02_unauthenticated_access_rejected():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/gamification")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_03_new_user_initializes_safely():
    user_id = await create_test_user("test3")
    async with TestSessionLocal() as db:
        service = GamificationService()
        g = await service.get_or_create_user_gamification(db, user_id=user_id)
        assert g.user_id == user_id
        assert g.xp == 0
        assert g.level == 1
        assert g.problems_solved == 0
        assert g.successful_submissions == 0
        assert g.current_streak == 0
        assert g.longest_streak == 0
        assert g.last_activity_date is None


@pytest.mark.asyncio
async def test_04_easy_first_solve_awards_10_xp():
    user_id = await create_test_user("test4")
    async with TestSessionLocal() as db:
        prob = (await db.execute(select(Problem).where(Problem.difficulty == ProblemDifficulty.EASY))).scalars().first()
        sub = Submission(
            user_id=user_id,
            problem_id=prob.id,
            language="PYTHON",
            source_code="print('test')",
            status="PASSED",
            total_tests=1,
            passed_tests=1,
            failed_tests=0,
            created_at=datetime.now(timezone.utc),
        )
        db.add(sub)
        await db.commit()
        await db.refresh(sub)

        service = GamificationService()
        g = await service.process_submission_for_gamification(db, sub)
        await db.commit()

        assert g.xp == 10
        assert g.level == 1


@pytest.mark.asyncio
async def test_05_medium_first_solve_awards_25_xp():
    user_id = await create_test_user("test5")
    async with TestSessionLocal() as db:
        prob = (await db.execute(select(Problem).where(Problem.difficulty == ProblemDifficulty.MEDIUM))).scalars().first()
        sub = Submission(
            user_id=user_id,
            problem_id=prob.id,
            language="PYTHON",
            source_code="print('medium')",
            status="PASSED",
            total_tests=1,
            passed_tests=1,
            failed_tests=0,
            created_at=datetime.now(timezone.utc),
        )
        db.add(sub)
        await db.commit()
        await db.refresh(sub)

        service = GamificationService()
        g = await service.process_submission_for_gamification(db, sub)
        await db.commit()

        assert g.xp == 25


@pytest.mark.asyncio
async def test_06_hard_first_solve_awards_50_xp():
    user_id = await create_test_user("test6")
    async with TestSessionLocal() as db:
        prob = (await db.execute(select(Problem).where(Problem.difficulty == ProblemDifficulty.HARD))).scalars().first()
        sub = Submission(
            user_id=user_id,
            problem_id=prob.id,
            language="PYTHON",
            source_code="print('hard')",
            status="PASSED",
            total_tests=1,
            passed_tests=1,
            failed_tests=0,
            created_at=datetime.now(timezone.utc),
        )
        db.add(sub)
        await db.commit()
        await db.refresh(sub)

        service = GamificationService()
        g = await service.process_submission_for_gamification(db, sub)
        await db.commit()

        assert g.xp == 50


@pytest.mark.asyncio
async def test_07_first_solve_increments_problems_solved():
    user_id = await create_test_user("test7")
    async with TestSessionLocal() as db:
        prob = (await db.execute(select(Problem))).scalars().first()
        sub = Submission(
            user_id=user_id,
            problem_id=prob.id,
            language="PYTHON",
            source_code="print('test')",
            status="PASSED",
            total_tests=1,
            passed_tests=1,
            failed_tests=0,
            created_at=datetime.now(timezone.utc),
        )
        db.add(sub)
        await db.commit()
        await db.refresh(sub)

        service = GamificationService()
        g = await service.process_submission_for_gamification(db, sub)
        await db.commit()

        assert g.problems_solved == 1


@pytest.mark.asyncio
async def test_08_repeated_solve_does_not_increment_problems_solved():
    user_id = await create_test_user("test8")
    async with TestSessionLocal() as db:
        prob = (await db.execute(select(Problem))).scalars().first()

        # First solve
        sub1 = Submission(
            user_id=user_id,
            problem_id=prob.id,
            language="PYTHON",
            source_code="print('solve 1')",
            status="PASSED",
            total_tests=1,
            passed_tests=1,
            failed_tests=0,
            created_at=datetime.now(timezone.utc),
        )
        db.add(sub1)
        await db.commit()
        await db.refresh(sub1)

        service = GamificationService()
        await service.process_submission_for_gamification(db, sub1)
        await db.commit()

        # Second solve of same problem
        sub2 = Submission(
            user_id=user_id,
            problem_id=prob.id,
            language="PYTHON",
            source_code="print('solve 2')",
            status="PASSED",
            total_tests=1,
            passed_tests=1,
            failed_tests=0,
            created_at=datetime.now(timezone.utc),
        )
        db.add(sub2)
        await db.commit()
        await db.refresh(sub2)

        g2 = await service.process_submission_for_gamification(db, sub2)
        await db.commit()

        assert g2.problems_solved == 1


@pytest.mark.asyncio
async def test_09_repeated_solve_does_not_award_xp_again():
    user_id = await create_test_user("test9")
    async with TestSessionLocal() as db:
        prob = (await db.execute(select(Problem).where(Problem.difficulty == ProblemDifficulty.EASY))).scalars().first()
        service = GamificationService()

        # Solve 1
        sub1 = Submission(
            user_id=user_id,
            problem_id=prob.id,
            language="PYTHON",
            source_code="print('solve 1')",
            status="PASSED",
            total_tests=1,
            passed_tests=1,
            failed_tests=0,
            created_at=datetime.now(timezone.utc),
        )
        db.add(sub1)
        await db.commit()
        await db.refresh(sub1)

        g1 = await service.process_submission_for_gamification(db, sub1)
        await db.commit()
        initial_xp = g1.xp

        # Solve 2 of same problem
        sub2 = Submission(
            user_id=user_id,
            problem_id=prob.id,
            language="PYTHON",
            source_code="print('solve 2')",
            status="PASSED",
            total_tests=1,
            passed_tests=1,
            failed_tests=0,
            created_at=datetime.now(timezone.utc),
        )
        db.add(sub2)
        await db.commit()
        await db.refresh(sub2)

        g2 = await service.process_submission_for_gamification(db, sub2)
        await db.commit()

        assert g2.xp == initial_xp


@pytest.mark.asyncio
async def test_10_successful_submissions_count_correctly():
    user_id = await create_test_user("test10")
    async with TestSessionLocal() as db:
        prob = (await db.execute(select(Problem))).scalars().first()
        service = GamificationService()

        # Solve 1
        sub1 = Submission(
            user_id=user_id,
            problem_id=prob.id,
            language="PYTHON",
            source_code="print('1')",
            status="PASSED",
            total_tests=1,
            passed_tests=1,
            failed_tests=0,
            created_at=datetime.now(timezone.utc),
        )
        db.add(sub1)
        await db.commit()
        await db.refresh(sub1)
        await service.process_submission_for_gamification(db, sub1)
        await db.commit()

        # Solve 2
        sub2 = Submission(
            user_id=user_id,
            problem_id=prob.id,
            language="PYTHON",
            source_code="print('2')",
            status="PASSED",
            total_tests=1,
            passed_tests=1,
            failed_tests=0,
            created_at=datetime.now(timezone.utc),
        )
        db.add(sub2)
        await db.commit()
        await db.refresh(sub2)
        g2 = await service.process_submission_for_gamification(db, sub2)
        await db.commit()

        assert g2.successful_submissions == 2


@pytest.mark.asyncio
async def test_11_same_day_activity_does_not_increment_streak():
    user_id = await create_test_user("test11")
    today = datetime.now(timezone.utc)
    async with TestSessionLocal() as db:
        probs = (await db.execute(select(Problem))).scalars().all()
        service = GamificationService()

        for i in range(3):
            sub = Submission(
                user_id=user_id,
                problem_id=probs[i].id,
                language="PYTHON",
                source_code=f"print({i})",
                status="PASSED",
                total_tests=1,
                passed_tests=1,
                failed_tests=0,
                created_at=today,
            )
            db.add(sub)
            await db.commit()
            await db.refresh(sub)
            g = await service.process_submission_for_gamification(db, sub)
            await db.commit()

        assert g.current_streak == 1
        assert g.longest_streak == 1


@pytest.mark.asyncio
async def test_12_consecutive_day_activity_increments_streak():
    user_id = await create_test_user("test12")
    base_time = datetime(2026, 9, 20, 12, 0, 0, tzinfo=timezone.utc)
    async with TestSessionLocal() as db:
        probs = (await db.execute(select(Problem))).scalars().all()
        service = GamificationService()

        # Day 1
        sub1 = Submission(
            user_id=user_id,
            problem_id=probs[0].id,
            language="PYTHON",
            source_code="day 1",
            status="PASSED",
            total_tests=1,
            passed_tests=1,
            failed_tests=0,
            created_at=base_time,
        )
        db.add(sub1)
        await db.commit()
        await db.refresh(sub1)
        g1 = await service.process_submission_for_gamification(db, sub1)
        await db.commit()
        assert g1.current_streak == 1

        # Day 2 (consecutive)
        sub2 = Submission(
            user_id=user_id,
            problem_id=probs[1].id,
            language="PYTHON",
            source_code="day 2",
            status="PASSED",
            total_tests=1,
            passed_tests=1,
            failed_tests=0,
            created_at=base_time + timedelta(days=1),
        )
        db.add(sub2)
        await db.commit()
        await db.refresh(sub2)
        g2 = await service.process_submission_for_gamification(db, sub2)
        await db.commit()
        assert g2.current_streak == 2
        assert g2.longest_streak == 2


@pytest.mark.asyncio
async def test_13_missed_day_resets_streak():
    user_id = await create_test_user("test13")
    base_time = datetime(2026, 9, 20, 12, 0, 0, tzinfo=timezone.utc)
    async with TestSessionLocal() as db:
        probs = (await db.execute(select(Problem))).scalars().all()
        service = GamificationService()

        # Day 1
        sub1 = Submission(
            user_id=user_id,
            problem_id=probs[0].id,
            language="PYTHON",
            source_code="day 1",
            status="PASSED",
            total_tests=1,
            passed_tests=1,
            failed_tests=0,
            created_at=base_time,
        )
        db.add(sub1)
        await db.commit()
        await db.refresh(sub1)
        await service.process_submission_for_gamification(db, sub1)
        await db.commit()

        # Day 3 (missed day 2)
        sub3 = Submission(
            user_id=user_id,
            problem_id=probs[1].id,
            language="PYTHON",
            source_code="day 3",
            status="PASSED",
            total_tests=1,
            passed_tests=1,
            failed_tests=0,
            created_at=base_time + timedelta(days=2),
        )
        db.add(sub3)
        await db.commit()
        await db.refresh(sub3)
        g3 = await service.process_submission_for_gamification(db, sub3)
        await db.commit()

        assert g3.current_streak == 1


@pytest.mark.asyncio
async def test_14_longest_streak_is_preserved():
    user_id = await create_test_user("test14")
    base_time = datetime(2026, 9, 20, 12, 0, 0, tzinfo=timezone.utc)
    async with TestSessionLocal() as db:
        probs = (await db.execute(select(Problem))).scalars().all()
        service = GamificationService()

        # 3 consecutive days
        for i in range(3):
            sub = Submission(
                user_id=user_id,
                problem_id=probs[i].id,
                language="PYTHON",
                source_code=f"day {i}",
                status="PASSED",
                total_tests=1,
                passed_tests=1,
                failed_tests=0,
                created_at=base_time + timedelta(days=i),
            )
            db.add(sub)
            await db.commit()
            await db.refresh(sub)
            await service.process_submission_for_gamification(db, sub)
            await db.commit()

        # Skip a day, then activity on day 5
        sub_break = Submission(
            user_id=user_id,
            problem_id=probs[3].id,
            language="PYTHON",
            source_code="day 5",
            status="PASSED",
            total_tests=1,
            passed_tests=1,
            failed_tests=0,
            created_at=base_time + timedelta(days=4),
        )
        db.add(sub_break)
        await db.commit()
        await db.refresh(sub_break)
        g_final = await service.process_submission_for_gamification(db, sub_break)
        await db.commit()

        assert g_final.current_streak == 1
        assert g_final.longest_streak == 3


def test_15_level_calculation_is_correct():
    calc = GamificationService.calculate_level
    assert calc(0) == 1
    assert calc(50) == 1
    assert calc(99) == 1
    assert calc(100) == 2
    assert calc(199) == 2
    assert calc(200) == 3
    assert calc(250) == 3
    assert calc(1000) == 11


@pytest.mark.asyncio
async def test_16_cross_user_data_is_protected():
    user1_id = await create_test_user("user_a")
    user2_id = await create_test_user("user_b")

    # User 1 solves a problem
    async with TestSessionLocal() as db:
        prob = (await db.execute(select(Problem))).scalars().first()
        sub = Submission(
            user_id=user1_id,
            problem_id=prob.id,
            language="PYTHON",
            source_code="user a solve",
            status="PASSED",
            total_tests=1,
            passed_tests=1,
            failed_tests=0,
            created_at=datetime.now(timezone.utc),
        )
        db.add(sub)
        await db.commit()
        await db.refresh(sub)
        service = GamificationService()
        await service.process_submission_for_gamification(db, sub)
        await db.commit()

    # User 1 endpoint check
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res1 = await ac.get("/api/v1/gamification", headers=get_auth_header(user1_id))
        res2 = await ac.get("/api/v1/gamification", headers=get_auth_header(user2_id))

    assert res1.status_code == 200
    assert res2.status_code == 200

    data1 = res1.json()
    data2 = res2.json()

    assert data1["user_id"] == user1_id
    assert data1["problems_solved"] == 1
    assert data2["user_id"] == user2_id
    assert data2["problems_solved"] == 0


@pytest.mark.asyncio
async def test_17_existing_submission_slre_behavior_remains_intact(monkeypatch):
    user_id = await create_test_user("test17")
    async with TestSessionLocal() as db:
        prob = (await db.execute(select(Problem))).scalars().first()

        submission_service = SubmissionService()
        mock_exec_res = ExecutionResponse(
            language="PYTHON",
            status="PASSED",
            total_tests=1,
            passed_tests=1,
            failed_tests=0,
            execution_time_ms=10.0,
            memory_used_mb=5.0,
            test_results=[
                TestResultItem(
                    test_number=1,
                    status="PASSED",
                    execution_time_ms=10.0,
                    actual_output="10",
                    expected_output="10",
                    error_message=None,
                    is_hidden=False,
                )
            ],
        )
        monkeypatch.setattr(
            submission_service.execution_service,
            "execute_code",
            AsyncMock(return_value=mock_exec_res),
        )

        req = SubmissionCreate(
            problem_id=prob.id,
            language="PYTHON",
            source_code="print('Hello World')",
        )
        resp = await submission_service.create_submission(db, user_id=user_id, request=req)

        assert resp.id is not None
        assert resp.user_id == user_id
        assert resp.problem_id == prob.id
        assert resp.status == "PASSED"

        # Verify gamification record updated as part of submission flow
        service = GamificationService()
        g = await service.get_or_create_user_gamification(db, user_id=user_id)
        assert g.successful_submissions == 1
        assert g.problems_solved == 1


@pytest.mark.asyncio
async def test_18_same_day_multiple_solves_does_not_award_three_day_streak():
    user_id = await create_test_user("test18")
    today = datetime.now(timezone.utc)
    async with TestSessionLocal() as db:
        probs = (await db.execute(select(Problem))).scalars().all()
        service = GamificationService()

        # Solve 3 problems on the exact same calendar day
        for i in range(3):
            sub = Submission(
                user_id=user_id,
                problem_id=probs[i].id,
                language="PYTHON",
                source_code=f"same day {i}",
                status="PASSED",
                total_tests=1,
                passed_tests=1,
                failed_tests=0,
                created_at=today,
            )
            db.add(sub)
            await db.commit()
            await db.refresh(sub)
            g = await service.process_submission_for_gamification(db, sub)
            await db.commit()

        assert g.problems_solved == 3
        assert g.current_streak == 1
        assert "THREE_DAY_STREAK" not in (g.badges or [])


@pytest.mark.asyncio
async def test_19_genuine_three_day_streak_awards_three_day_streak_badge():
    user_id = await create_test_user("test19")
    base_time = datetime(2026, 9, 20, 12, 0, 0, tzinfo=timezone.utc)
    async with TestSessionLocal() as db:
        probs = (await db.execute(select(Problem))).scalars().all()
        service = GamificationService()

        for i in range(3):
            sub = Submission(
                user_id=user_id,
                problem_id=probs[i].id,
                language="PYTHON",
                source_code=f"day {i}",
                status="PASSED",
                total_tests=1,
                passed_tests=1,
                failed_tests=0,
                created_at=base_time + timedelta(days=i),
            )
            db.add(sub)
            await db.commit()
            await db.refresh(sub)
            g = await service.process_submission_for_gamification(db, sub)
            await db.commit()

        assert g.current_streak == 3
        assert "THREE_DAY_STREAK" in (g.badges or [])


@pytest.mark.asyncio
async def test_20_seven_solves_without_seven_day_streak_does_not_award_seven_day_streak():
    user_id = await create_test_user("test20")
    today = datetime.now(timezone.utc)
    async with TestSessionLocal() as db:
        probs = (await db.execute(select(Problem))).scalars().all()
        service = GamificationService()

        # Solve 7 problems on the same day
        for i in range(7):
            sub = Submission(
                user_id=user_id,
                problem_id=probs[i].id,
                language="PYTHON",
                source_code=f"same day solve {i}",
                status="PASSED",
                total_tests=1,
                passed_tests=1,
                failed_tests=0,
                created_at=today,
            )
            db.add(sub)
            await db.commit()
            await db.refresh(sub)
            g = await service.process_submission_for_gamification(db, sub)
            await db.commit()

        assert g.problems_solved == 7
        assert g.current_streak == 1
        assert "SEVEN_DAY_STREAK" not in (g.badges or [])


@pytest.mark.asyncio
async def test_21_genuine_seven_day_streak_awards_seven_day_streak_badge():
    user_id = await create_test_user("test21")
    base_time = datetime(2026, 9, 10, 12, 0, 0, tzinfo=timezone.utc)
    async with TestSessionLocal() as db:
        probs = (await db.execute(select(Problem))).scalars().all()
        service = GamificationService()

        for i in range(7):
            sub = Submission(
                user_id=user_id,
                problem_id=probs[i].id,
                language="PYTHON",
                source_code=f"day {i}",
                status="PASSED",
                total_tests=1,
                passed_tests=1,
                failed_tests=0,
                created_at=base_time + timedelta(days=i),
            )
            db.add(sub)
            await db.commit()
            await db.refresh(sub)
            g = await service.process_submission_for_gamification(db, sub)
            await db.commit()

        assert g.current_streak == 7
        assert "SEVEN_DAY_STREAK" in (g.badges or [])
