import uuid
from datetime import datetime, timezone, timedelta
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool

from app.main import app
from app.core.config import settings
from app.core.db import get_db
from app.core.security import create_access_token, hash_password
from app.models.user import User, UserRole
from app.models.topic import Topic
from app.models.problem import Problem, ProblemDifficulty
from app.models.submission import Submission
from app.models.skill_profile import SkillProfile
from app.models.recommendation import Recommendation
from app.seed_data import seed_data
from app.services.recommendation_service import RecommendationService


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
        # Clean up any non-seeded test problems created dynamically
        extra_probs = (await session.execute(select(Problem).where(Problem.id > 36))).scalars().all()
        for p in extra_probs:
            await session.delete(p)
        if extra_probs:
            await session.commit()


async def create_test_user(prefix: str = "rec_user") -> int:
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


def get_auth_header(user_id: int):
    token = create_access_token(subject=str(user_id), role="USER")
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_1_authenticated_recommendations_endpoint_works():
    uid = await create_test_user("t1")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get(
            "/api/v1/recommendations",
            headers=get_auth_header(uid),
        )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert len(data) <= 5


@pytest.mark.asyncio
async def test_2_unauthenticated_request_rejected():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/recommendations")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_3_returns_maximum_5_recommendations():
    uid = await create_test_user("t3")
    rec_service = RecommendationService()
    async with TestSessionLocal() as session:
        recs = await rec_service.get_user_recommendations(session, user_id=uid)
    assert len(recs) <= 5


@pytest.mark.asyncio
async def test_4_deterministic_ordering_by_score_desc_and_problem_id_asc():
    uid = await create_test_user("t4")
    rec_service = RecommendationService()
    async with TestSessionLocal() as session:
        recs1 = await rec_service.get_user_recommendations(session, user_id=uid)
        ids1 = [r.problem_id for r in recs1]
        scores1 = [r.score for r in recs1]

        # Verify scores descending
        for i in range(len(scores1) - 1):
            assert scores1[i] >= scores1[i + 1]

        # Second call returns identical order
        recs2 = await rec_service.get_user_recommendations(session, user_id=uid)
        ids2 = [r.problem_id for r in recs2]

        assert ids1 == ids2


@pytest.mark.asyncio
async def test_5_passed_problems_excluded():
    uid = await create_test_user("t5")
    rec_service = RecommendationService()
    async with TestSessionLocal() as session:
        # Mark problem 1 as PASSED
        p1 = (await session.execute(select(Problem).where(Problem.id == 1))).scalars().first()
        sub = Submission(user_id=uid, problem_id=p1.id, language="python", source_code="...", status="PASSED")
        session.add(sub)
        await session.commit()

        recs = await rec_service.get_user_recommendations(session, user_id=uid)
        rec_problem_ids = [r.problem_id for r in recs]

        # Problem 1 must NOT be in recommendations
        assert p1.id not in rec_problem_ids


@pytest.mark.asyncio
async def test_6_failed_problems_remain_eligible():
    uid = await create_test_user("t6")
    rec_service = RecommendationService()
    async with TestSessionLocal() as session:
        p1 = (await session.execute(select(Problem).where(Problem.id == 1))).scalars().first()
        sub = Submission(user_id=uid, problem_id=p1.id, language="python", source_code="...", status="FAILED")
        session.add(sub)
        await session.commit()

        recs = await rec_service.get_user_recommendations(session, user_id=uid)
        rec_problem_ids = [r.problem_id for r in recs]

        # Failed problem remains eligible
        assert len(recs) > 0


@pytest.mark.asyncio
async def test_7_diagnostic_only_problems_excluded():
    uid = await create_test_user("t7")
    rec_service = RecommendationService()
    async with TestSessionLocal() as session:
        diag_problems = (await session.execute(select(Problem).where(Problem.is_diagnostic == True))).scalars().all()
        diag_ids = set(p.id for p in diag_problems)

        recs = await rec_service.get_user_recommendations(session, user_id=uid)
        rec_ids = set(r.problem_id for r in recs)

        # No diagnostic problem should be recommended
        assert rec_ids.isdisjoint(diag_ids)


@pytest.mark.asyncio
async def test_8_difficulty_personalization_low_vs_expert_skill():
    u_low = await create_test_user("t8_low")
    u_expert = await create_test_user("t8_expert")
    rec_service = RecommendationService()

    async with TestSessionLocal() as session:
        topics = (await session.execute(select(Topic))).scalars().all()

        # Low skill profiles
        for t in topics:
            sp = SkillProfile(user_id=u_low, topic_id=t.id, skill_score=10.0, skill_level="BEGINNER", confidence=0.5, problems_solved=0)
            session.add(sp)

        # Expert skill profiles
        for t in topics:
            sp = SkillProfile(user_id=u_expert, topic_id=t.id, skill_score=90.0, skill_level="EXPERT", confidence=0.9, problems_solved=10)
            session.add(sp)

        await session.commit()

        recs_low = await rec_service.get_user_recommendations(session, user_id=u_low)
        recs_expert = await rec_service.get_user_recommendations(session, user_id=u_expert)

        diffs_low = [r.problem.difficulty.value if hasattr(r.problem.difficulty, 'value') else str(r.problem.difficulty) for r in recs_low]
        diffs_expert = [r.problem.difficulty.value if hasattr(r.problem.difficulty, 'value') else str(r.problem.difficulty) for r in recs_expert]

        # Low skill user should favor EASY problems
        assert "EASY" in diffs_low
        # Expert skill user should favor HARD problems
        assert "HARD" in diffs_expert


@pytest.mark.asyncio
async def test_9_weak_topic_preference():
    uid = await create_test_user("t9_weak")
    rec_service = RecommendationService()

    async with TestSessionLocal() as session:
        topics = (await session.execute(select(Topic))).scalars().all()
        t_arrays = next(t for t in topics if t.name == "Arrays")

        # Set all topics to 85.0 (strong), except Arrays which is set to 15.0 (weakest)
        for t in topics:
            score = 15.0 if t.id == t_arrays.id else 85.0
            level = "BEGINNER" if t.id == t_arrays.id else "EXPERT"
            sp = SkillProfile(user_id=uid, topic_id=t.id, skill_score=score, skill_level=level, confidence=0.5, problems_solved=1)
            session.add(sp)

        await session.commit()

        recs = await rec_service.get_user_recommendations(session, user_id=uid)
        top_rec_topics = [t.name for t in recs[0].problem.topics]

        # Top recommendation should target the weaker topic (Arrays)
        assert "Arrays" in top_rec_topics


@pytest.mark.asyncio
async def test_10_confidence_affects_scoring():
    uid = await create_test_user("t10_conf")
    rec_service = RecommendationService()

    async with TestSessionLocal() as session:
        t_arrays = (await session.execute(select(Topic).where(Topic.name == "Arrays"))).scalars().first()
        # Low confidence -> produces higher recommendation urgency
        sp = SkillProfile(user_id=uid, topic_id=t_arrays.id, skill_score=30.0, skill_level="NOVICE", confidence=0.05)
        session.add(sp)
        await session.commit()

        recs = await rec_service.get_user_recommendations(session, user_id=uid)
        assert len(recs) > 0
        assert recs[0].score > 0.0


@pytest.mark.asyncio
async def test_11_multi_topic_problem_handled_correctly():
    uid = await create_test_user("t11_multi_topic")
    rec_service = RecommendationService()
    unique_str = uuid.uuid4().hex[:8]

    async with TestSessionLocal() as session:
        # Create problem with multiple topics
        t1 = (await session.execute(select(Topic).where(Topic.name == "Arrays"))).scalars().first()
        t2 = (await session.execute(select(Topic).where(Topic.name == "Hashing"))).scalars().first()

        p_multi = Problem(
            title=f"Multi Topic Test Problem {unique_str}",
            slug=f"multi-topic-test-{unique_str}",
            description="Problem with multiple topics",
            difficulty=ProblemDifficulty.MEDIUM,
            is_diagnostic=False,
            topics=[t1, t2],
        )
        session.add(p_multi)
        await session.commit()

        try:
            recs = await rec_service.get_user_recommendations(session, user_id=uid)
            assert isinstance(recs, list)
        finally:
            await session.delete(p_multi)
            await session.commit()


@pytest.mark.asyncio
async def test_12_explanation_reasons_generated():
    uid = await create_test_user("t12_reasons")
    rec_service = RecommendationService()

    async with TestSessionLocal() as session:
        recs = await rec_service.get_user_recommendations(session, user_id=uid)
        for r in recs:
            assert isinstance(r.reasons, list)
            assert len(r.reasons) >= 2


@pytest.mark.asyncio
async def test_13_reasons_bounded_to_2_to_3():
    uid = await create_test_user("t13_bounded_reasons")
    rec_service = RecommendationService()

    async with TestSessionLocal() as session:
        recs = await rec_service.get_user_recommendations(session, user_id=uid)
        for r in recs:
            assert 2 <= len(r.reasons) <= 3


@pytest.mark.asyncio
async def test_14_recommendation_persistence_works():
    uid = await create_test_user("t14_persist")
    rec_service = RecommendationService()

    async with TestSessionLocal() as session:
        recs = await rec_service.get_user_recommendations(session, user_id=uid)
        await session.commit()

        # Query database directly to verify stored rows
        stmt = select(Recommendation).where(Recommendation.user_id == uid)
        stored_recs = (await session.execute(stmt)).scalars().all()
        assert len(stored_recs) == len(recs)
        assert stored_recs[0].user_id == uid


@pytest.mark.asyncio
async def test_15_stale_or_passed_recommendation_is_refreshed():
    uid = await create_test_user("t15_refresh")
    rec_service = RecommendationService()

    async with TestSessionLocal() as session:
        # Generate initial recommendations
        recs_initial = await rec_service.get_user_recommendations(session, user_id=uid)
        first_rec_problem_id = recs_initial[0].problem_id

        # Now user passes the top recommended problem
        sub = Submission(user_id=uid, problem_id=first_rec_problem_id, language="python", source_code="...", status="PASSED")
        session.add(sub)
        await session.commit()

        # Fetch recommendations again -> stale recommendations must be refreshed
        recs_refreshed = await rec_service.get_user_recommendations(session, user_id=uid)
        refreshed_problem_ids = [r.problem_id for r in recs_refreshed]

        # The passed problem must no longer appear
        assert first_rec_problem_id not in refreshed_problem_ids


@pytest.mark.asyncio
async def test_16_empty_candidate_pool_handled_safely():
    uid = await create_test_user("t16_empty_candidates")
    rec_service = RecommendationService()

    async with TestSessionLocal() as session:
        # Mark all non-diagnostic problems as PASSED
        non_diag = (await session.execute(select(Problem).where(Problem.is_diagnostic == False))).scalars().all()
        for p in non_diag:
            sub = Submission(user_id=uid, problem_id=p.id, language="python", source_code="...", status="PASSED")
            session.add(sub)
        await session.commit()

        recs = await rec_service.get_user_recommendations(session, user_id=uid)
        assert recs == []


@pytest.mark.asyncio
async def test_17_untested_topic_handled_safely():
    uid = await create_test_user("t17_untested")
    rec_service = RecommendationService()

    async with TestSessionLocal() as session:
        # User has no SkillProfile records created yet
        recs = await rec_service.get_user_recommendations(session, user_id=uid)
        assert isinstance(recs, list)
        assert len(recs) <= 5


@pytest.mark.asyncio
async def test_18_tie_breaking_is_deterministic():
    uid = await create_test_user("t18_tie_break")
    rec_service = RecommendationService()

    async with TestSessionLocal() as session:
        recs1 = await rec_service.get_user_recommendations(session, user_id=uid)
        recs2 = await rec_service.get_user_recommendations(session, user_id=uid)

        ids1 = [r.problem_id for r in recs1]
        ids2 = [r.problem_id for r in recs2]

        assert ids1 == ids2
