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
from app.seed_data import seed_data
from app.services.slre_service import SLREService, compute_skill_level_name


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


async def create_test_user(prefix: str = "user") -> int:
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
async def test_1_unauthenticated_skill_api_rejected():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/skills")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_2_authenticated_user_can_retrieve_skill_profiles():
    uid = await create_test_user("t2")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get(
            "/api/v1/skills",
            headers=get_auth_header(uid),
        )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 12


@pytest.mark.asyncio
async def test_3_exactly_12_topic_profiles_after_diagnostic_completion():
    uid = await create_test_user("t3")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Start & submit diagnostic
        start_resp = await ac.post("/api/v1/diagnostic/start", headers=get_auth_header(uid))
        ass_data = start_resp.json()
        ass_id = ass_data["assessment_id"]
        questions = ass_data["questions"]

        answers = [{"problem_id": q["problem_id"], "selected_answer": "C"} for q in questions]
        await ac.post(f"/api/v1/diagnostic/{ass_id}/submit", headers=get_auth_header(uid), json={"answers": answers})

        # Fetch skills
        skills_resp = await ac.get("/api/v1/skills", headers=get_auth_header(uid))

    assert skills_resp.status_code == 200
    skills = skills_resp.json()
    assert len(skills) == 12


@pytest.mark.asyncio
async def test_4_no_duplicate_user_topic_skill_profiles():
    uid = await create_test_user("t4")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Call get /skills multiple times
        await ac.get("/api/v1/skills", headers=get_auth_header(uid))
        await ac.get("/api/v1/skills", headers=get_auth_header(uid))

    async with TestSessionLocal() as session:
        stmt = select(SkillProfile).where(SkillProfile.user_id == uid)
        profiles = (await session.execute(stmt)).scalars().all()
        assert len(profiles) == 12
        topic_ids = [p.topic_id for p in profiles]
        assert len(topic_ids) == len(set(topic_ids))


@pytest.mark.asyncio
async def test_5_diagnostic_responses_update_appropriate_topic_skills():
    uid = await create_test_user("t5")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        start_resp = await ac.post("/api/v1/diagnostic/start", headers=get_auth_header(uid))
        ass_data = start_resp.json()
        ass_id = ass_data["assessment_id"]
        questions = ass_data["questions"]

        # Submit valid diagnostic answers
        answers = [{"problem_id": q["problem_id"], "selected_answer": "C" if q["problem_id"] == 1 else "A"} for q in questions]
        await ac.post(f"/api/v1/diagnostic/{ass_id}/submit", headers=get_auth_header(uid), json={"answers": answers})

        skills_resp = await ac.get("/api/v1/skills", headers=get_auth_header(uid))

    skills = skills_resp.json()
    # Topic 1 (Arrays) should have updated confidence >= 0.30
    arrays_skill = next(s for s in skills if s["topic_name"] == "Arrays")
    assert arrays_skill["confidence"] >= 0.30
    assert arrays_skill["skill_score"] > 0


@pytest.mark.asyncio
async def test_6_untested_topics_greedy_and_dp_receive_neutral_default_initialization():
    uid = await create_test_user("t6")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        start_resp = await ac.post("/api/v1/diagnostic/start", headers=get_auth_header(uid))
        ass_data = start_resp.json()
        ass_id = ass_data["assessment_id"]
        questions = ass_data["questions"]

        answers = [{"problem_id": q["problem_id"], "selected_answer": "C"} for q in questions]
        await ac.post(f"/api/v1/diagnostic/{ass_id}/submit", headers=get_auth_header(uid), json={"answers": answers})

        skills_resp = await ac.get("/api/v1/skills", headers=get_auth_header(uid))

    skills = skills_resp.json()
    greedy_skill = next(s for s in skills if s["topic_name"] == "Greedy")
    dp_skill = next(s for s in skills if s["topic_name"] == "Dynamic Programming")

    assert greedy_skill["confidence"] == 0.05
    assert greedy_skill["skill_score"] == 10.0
    assert dp_skill["confidence"] == 0.05
    assert dp_skill["skill_score"] == 10.0


@pytest.mark.asyncio
async def test_7_correct_coding_submission_updates_relevant_skill():
    uid = await create_test_user("t7")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        sub_resp = await ac.post(
            "/api/v1/submissions",
            headers=get_auth_header(uid),
            json={
                "problem_id": 1,
                "language": "python",
                "source_code": "import sys\nnums = list(map(int, sys.stdin.read().split()))\nprint(max(nums))\n",
            },
        )
        assert sub_resp.status_code == 201
        assert sub_resp.json()["status"] == "PASSED"

        skills_resp = await ac.get("/api/v1/skills", headers=get_auth_header(uid))

    skills = skills_resp.json()
    arrays_skill = next(s for s in skills if s["topic_name"] == "Arrays")
    assert arrays_skill["problems_solved"] == 1
    assert arrays_skill["total_points"] == 10
    assert arrays_skill["skill_score"] > 10.0


@pytest.mark.asyncio
async def test_8_incorrect_submission_updates_evidence_without_destroying_profile():
    uid = await create_test_user("t8")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        b1 = (await ac.get("/api/v1/skills", headers=get_auth_header(uid))).json()
        b_arrays = next(s for s in b1 if s["topic_name"] == "Arrays")
        orig_score = b_arrays["skill_score"]

        sub_resp = await ac.post(
            "/api/v1/submissions",
            headers=get_auth_header(uid),
            json={
                "problem_id": 1,
                "language": "python",
                "source_code": "import sys\nprint(-999)\n",
            },
        )
        assert sub_resp.status_code == 201
        assert sub_resp.json()["status"] == "FAILED"

        b2 = (await ac.get("/api/v1/skills", headers=get_auth_header(uid))).json()
        updated_arrays = next(s for s in b2 if s["topic_name"] == "Arrays")

    assert updated_arrays["skill_score"] >= max(0.0, orig_score - 2.0)
    assert updated_arrays["confidence"] >= b_arrays["confidence"]


@pytest.mark.asyncio
async def test_9_harder_problems_provide_stronger_skill_evidence_than_easier_problems():
    u_easy_id = await create_test_user("t9_easy")
    u_hard_id = await create_test_user("t9_hard")
    slre = SLREService()

    async with TestSessionLocal() as session:
        p_easy = (await session.execute(select(Problem).where(Problem.difficulty == ProblemDifficulty.EASY))).scalars().first()
        p_hard = (await session.execute(select(Problem).where(Problem.difficulty == ProblemDifficulty.HARD))).scalars().first()

        sub_easy = Submission(user_id=u_easy_id, problem_id=p_easy.id, language="python", source_code="...", status="PASSED")
        sub_hard = Submission(user_id=u_hard_id, problem_id=p_hard.id, language="python", source_code="...", status="PASSED")

        session.add(sub_easy)
        session.add(sub_hard)
        await session.flush()

        sp_easy_list = await slre.process_submission_for_skills(session, sub_easy)
        sp_hard_list = await slre.process_submission_for_skills(session, sub_hard)

        await session.commit()

    sp_easy = sp_easy_list[0]
    sp_hard = sp_hard_list[0]

    assert sp_hard.skill_score > sp_easy.skill_score
    assert sp_hard.total_points > sp_easy.total_points


@pytest.mark.asyncio
async def test_10_same_submission_processed_twice_is_idempotent():
    uid = await create_test_user("t10_idempotent")
    slre = SLREService()

    async with TestSessionLocal() as session:
        p1 = (await session.execute(select(Problem).where(Problem.id == 1))).scalars().first()
        sub = Submission(user_id=uid, problem_id=p1.id, language="python", source_code="...", status="PASSED")
        session.add(sub)
        await session.flush()

        # First processing call
        res1 = await slre.process_submission_for_skills(session, sub)
        score1 = res1[0].skill_score
        conf1 = res1[0].confidence
        solved1 = res1[0].problems_solved
        pts1 = res1[0].total_points

        # Second processing call on EXACT same submission record
        res2 = await slre.process_submission_for_skills(session, sub)
        score2 = res2[0].skill_score
        conf2 = res2[0].confidence
        solved2 = res2[0].problems_solved
        pts2 = res2[0].total_points

        await session.commit()

    # Verify 100% idempotency
    assert solved1 == solved2 == 1
    assert pts1 == pts2 == 10
    assert score1 == score2
    assert conf1 == conf2


@pytest.mark.asyncio
async def test_11_users_cannot_access_another_users_skill_profiles():
    u1_id = await create_test_user("t11_1")
    u2_id = await create_test_user("t11_2")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp1 = await ac.get("/api/v1/skills/1", headers=get_auth_header(u1_id))
        assert resp1.status_code == 200
        data1 = resp1.json()
        assert data1["user_id"] == u1_id

        resp2 = await ac.get("/api/v1/skills/1", headers=get_auth_header(u2_id))
        assert resp2.status_code == 200
        data2 = resp2.json()
        assert data2["user_id"] == u2_id
        assert data2["user_id"] != u1_id


@pytest.mark.asyncio
async def test_12_slre_calculations_are_deterministic():
    assert compute_skill_level_name(15.0) == "BEGINNER"
    assert compute_skill_level_name(25.0) == "NOVICE"
    assert compute_skill_level_name(45.0) == "INTERMEDIATE"
    assert compute_skill_level_name(65.0) == "ADVANCED"
    assert compute_skill_level_name(85.0) == "EXPERT"


@pytest.mark.asyncio
async def test_13_attempt_signal_affects_slre_calculation():
    u_first = await create_test_user("t13_first_try")
    u_multi = await create_test_user("t13_multi_try")
    slre = SLREService()

    async with TestSessionLocal() as session:
        p1 = (await session.execute(select(Problem).where(Problem.id == 1))).scalars().first()

        # User First: passes on 1st attempt (0 failed attempts)
        sub_first = Submission(user_id=u_first, problem_id=p1.id, language="python", source_code="...", status="PASSED")
        session.add(sub_first)
        await session.flush()
        sp_first = (await slre.process_submission_for_skills(session, sub_first))[0]

        # User Multi: 3 failed attempts before passing
        for i in range(3):
            sub_fail = Submission(user_id=u_multi, problem_id=p1.id, language="python", source_code="...", status="FAILED")
            session.add(sub_fail)
            await session.flush()

        sub_pass_multi = Submission(user_id=u_multi, problem_id=p1.id, language="python", source_code="...", status="PASSED")
        session.add(sub_pass_multi)
        await session.flush()
        sp_multi = (await slre.process_submission_for_skills(session, sub_pass_multi))[0]

        await session.commit()

    # User who passed on 1st attempt receives a larger skill score gain than user who failed 3 times first
    assert sp_first.skill_score > sp_multi.skill_score


@pytest.mark.asyncio
async def test_14_recency_signal_affects_slre_calculation():
    u_recent = await create_test_user("t14_recent")
    u_old = await create_test_user("t14_old")
    slre = SLREService()

    async with TestSessionLocal() as session:
        p1 = (await session.execute(select(Problem).where(Problem.id == 1))).scalars().first()

        # Recent submission (created now)
        sub_recent = Submission(
            user_id=u_recent,
            problem_id=p1.id,
            language="python",
            source_code="...",
            status="PASSED",
            created_at=datetime.now(timezone.utc),
        )
        session.add(sub_recent)
        await session.flush()
        sp_recent = (await slre.process_submission_for_skills(session, sub_recent))[0]

        # Old submission (created 30 days ago)
        old_time = datetime.now(timezone.utc) - timedelta(days=30)
        sub_old = Submission(
            user_id=u_old,
            problem_id=p1.id,
            language="python",
            source_code="...",
            status="PASSED",
            created_at=old_time,
        )
        session.add(sub_old)
        await session.flush()
        sp_old = (await slre.process_submission_for_skills(session, sub_old))[0]

        await session.commit()

    # Recent submission gives higher skill score and confidence increase than 30-day-old submission
    assert sp_recent.skill_score > sp_old.skill_score
    assert sp_recent.confidence > sp_old.confidence


@pytest.mark.asyncio
async def test_15_later_diagnostic_does_not_erase_accumulated_coding_skill():
    uid = await create_test_user("t15_diagnostic_preserve")
    slre = SLREService()

    async with TestSessionLocal() as session:
        p1 = (await session.execute(select(Problem).where(Problem.id == 1))).scalars().first()

        # User completes coding submission first
        sub = Submission(user_id=uid, problem_id=p1.id, language="python", source_code="...", status="PASSED")
        session.add(sub)
        await session.flush()

        profiles_before = await slre.process_submission_for_skills(session, sub)
        orig_sp = profiles_before[0]
        orig_score = orig_sp.skill_score
        orig_level = orig_sp.skill_level
        orig_solved = orig_sp.problems_solved
        orig_points = orig_sp.total_points

        assert orig_score > 10.0
        assert orig_solved == 1
        assert orig_points == 10

        # Create dummy completed diagnostic assessment later
        from app.models.diagnostic_assessment import DiagnosticAssessment
        ass = DiagnosticAssessment(user_id=uid, status="COMPLETED", answered_questions=10, correct_answers=0, score=0.0)
        session.add(ass)
        await session.flush()

        # Run diagnostic skill initialization after coding activity
        profiles_after = await slre.initialize_skills_from_diagnostic(session, user_id=uid, assessment=ass)
        after_sp = next(p for p in profiles_after if p.topic_id == orig_sp.topic_id)

        await session.commit()

    # Verify accumulated coding skill, level, problems_solved, and total_points are NOT erased or reset
    assert after_sp.skill_score == orig_score
    assert after_sp.skill_level == orig_level
    assert after_sp.problems_solved == orig_solved
    assert after_sp.total_points == orig_points
