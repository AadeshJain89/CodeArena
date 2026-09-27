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
from app.models.problem import Problem
from app.models.diagnostic_assessment import DiagnosticAssessment
from app.models.diagnostic_response import DiagnosticResponse
from app.models.diagnostic_assessment_question import DiagnosticAssessmentQuestion
from app.seed_data import seed_data


test_engine = create_async_engine(settings.ASYNC_DATABASE_URI, poolclass=NullPool, echo=False)
TestSessionLocal = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db():
    async with TestSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


app.dependency_overrides[get_db] = override_get_db


USER1_ID = None
USER2_ID = None


@pytest_asyncio.fixture(autouse=True, scope="function")
async def ensure_seeded_db_and_users():
    global USER1_ID, USER2_ID
    async with TestSessionLocal() as session:
        await seed_data(session=session)

        # User 1
        res1 = await session.execute(select(User).where(User.username == "diag_user_1"))
        u1 = res1.scalar_one_or_none()
        if not u1:
            u1 = User(
                username="diag_user_1",
                email="diaguser1@example.com",
                password_hash=hash_password("Password123!"),
                role=UserRole.USER,
                is_active=True,
            )
            session.add(u1)
            await session.commit()
            await session.refresh(u1)
        USER1_ID = u1.id

        # User 2
        res2 = await session.execute(select(User).where(User.username == "diag_user_2"))
        u2 = res2.scalar_one_or_none()
        if not u2:
            u2 = User(
                username="diag_user_2",
                email="diaguser2@example.com",
                password_hash=hash_password("Password123!"),
                role=UserRole.USER,
                is_active=True,
            )
            session.add(u2)
            await session.commit()
            await session.refresh(u2)
        USER2_ID = u2.id


def get_auth_header(user_id):
    token = create_access_token(subject=str(user_id), role="USER")
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_1_unauthenticated_start_returns_401():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/diagnostic/start")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_2_authenticated_start_creates_assessment():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/diagnostic/start",
            headers=get_auth_header(USER1_ID),
        )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "IN_PROGRESS"
    assert data["total_questions"] == 10
    assert len(data["questions"]) == 10


@pytest.mark.asyncio
async def test_3_assessment_contains_exactly_10_persisted_questions():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        start_resp = await ac.post(
            "/api/v1/diagnostic/start",
            headers=get_auth_header(USER1_ID),
        )
    ass_id = start_resp.json()["assessment_id"]

    async with TestSessionLocal() as session:
        stmt = (
            select(DiagnosticAssessmentQuestion)
            .where(DiagnosticAssessmentQuestion.assessment_id == ass_id)
            .order_by(DiagnosticAssessmentQuestion.question_order.asc())
        )
        persisted_questions = (await session.execute(stmt)).scalars().all()
        assert len(persisted_questions) == 10
        orders = [q.question_order for q in persisted_questions]
        assert orders == list(range(1, 11))


@pytest.mark.asyncio
async def test_4_correct_answers_not_exposed_before_submission():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        start_resp = await ac.post(
            "/api/v1/diagnostic/start",
            headers=get_auth_header(USER1_ID),
        )
        data = start_resp.json()
        ass_id = data["assessment_id"]

        get_resp = await ac.get(
            f"/api/v1/diagnostic/{ass_id}",
            headers=get_auth_header(USER1_ID),
        )

    for resp_data in [data, get_resp.json()]:
        for q in resp_data["questions"]:
            assert "correct_option" not in q
            assert "diagnostic_correct_option" not in q
            assert "correct_answers" not in q


@pytest.mark.asyncio
async def test_5_user_can_retrieve_their_assessment():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        start_resp = await ac.post(
            "/api/v1/diagnostic/start",
            headers=get_auth_header(USER1_ID),
        )
        ass_id = start_resp.json()["assessment_id"]

        get_resp = await ac.get(
            f"/api/v1/diagnostic/{ass_id}",
            headers=get_auth_header(USER1_ID),
        )
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert data["assessment_id"] == ass_id
    assert data["status"] == "IN_PROGRESS"


@pytest.mark.asyncio
async def test_6_another_user_cannot_access_assessment():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        start_resp = await ac.post(
            "/api/v1/diagnostic/start",
            headers=get_auth_header(USER1_ID),
        )
        ass_id = start_resp.json()["assessment_id"]

        get_resp = await ac.get(
            f"/api/v1/diagnostic/{ass_id}",
            headers=get_auth_header(USER2_ID),
        )
    assert get_resp.status_code == 403


@pytest.mark.asyncio
async def test_7_assessment_retrieval_returns_exact_same_questions_and_order():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        start_resp = await ac.post(
            "/api/v1/diagnostic/start",
            headers=get_auth_header(USER1_ID),
        )
        start_data = start_resp.json()
        ass_id = start_data["assessment_id"]
        start_q_ids = [q["problem_id"] for q in start_data["questions"]]

        get_resp = await ac.get(
            f"/api/v1/diagnostic/{ass_id}",
            headers=get_auth_header(USER1_ID),
        )
        get_data = get_resp.json()
        get_q_ids = [q["problem_id"] for q in get_data["questions"]]

    assert get_q_ids == start_q_ids


@pytest.mark.asyncio
async def test_8_submission_validates_against_persisted_questions():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        start_resp = await ac.post(
            "/api/v1/diagnostic/start",
            headers=get_auth_header(USER1_ID),
        )
        ass_id = start_resp.json()["assessment_id"]

        invalid_answers = [{"problem_id": 999999, "selected_answer": "A"}]

        sub_resp = await ac.post(
            f"/api/v1/diagnostic/{ass_id}/submit",
            headers=get_auth_header(USER1_ID),
            json={"answers": invalid_answers},
        )
    assert sub_resp.status_code == 400
    assert "does not belong" in sub_resp.json()["detail"]


@pytest.mark.asyncio
async def test_9_correct_answers_are_evaluated_server_side():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        start_resp = await ac.post(
            "/api/v1/diagnostic/start",
            headers=get_auth_header(USER1_ID),
        )
        data = start_resp.json()
        ass_id = data["assessment_id"]
        questions = data["questions"]

        # Client submits answers without server correct options
        answers = [{"problem_id": q["problem_id"], "selected_answer": "INVALID_OPTION"} for q in questions]

        sub_resp = await ac.post(
            f"/api/v1/diagnostic/{ass_id}/submit",
            headers=get_auth_header(USER1_ID),
            json={"answers": answers},
        )
    assert sub_resp.status_code == 200
    res = sub_resp.json()
    assert res["status"] == "COMPLETED"
    assert res["correct_answers"] == 0
    assert res["score"] == 0.0


EXPECTED_SLUG_ANSWERS = {
    "find-maximum-element-in-array": "C",
    "reverse-string": "A",
    "two-sum-target-pair": "B",
    "valid-palindrome-string": "B",
    "maximum-average-subarray-i": "B",
    "valid-parentheses-string": "B",
    "reverse-singly-linked-list": "C",
    "standard-binary-search": "B",
    "maximum-depth-of-binary-tree": "D",
    "find-center-of-star-graph": "B",
}


@pytest.mark.asyncio
async def test_10_submission_produces_exact_expected_score():
    # 1. Verify seeded diagnostic questions against independent expected answer mapping by slug
    async with TestSessionLocal() as session:
        stmt = select(Problem).where(Problem.is_diagnostic == True)
        diag_probs = (await session.execute(stmt)).scalars().all()
        assert len(diag_probs) == 10
        problem_id_to_correct_opt = {}
        for p in diag_probs:
            assert p.slug in EXPECTED_SLUG_ANSWERS
            expected_opt = EXPECTED_SLUG_ANSWERS[p.slug]
            actual_opt = (p.diagnostic_correct_option or p.correct_option or "").strip().upper()
            assert actual_opt.startswith(expected_opt)
            problem_id_to_correct_opt[p.id] = expected_opt

    # 2. Start assessment via API
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        start_resp = await ac.post(
            "/api/v1/diagnostic/start",
            headers=get_auth_header(USER1_ID),
        )
        data = start_resp.json()
        ass_id = data["assessment_id"]
        questions = data["questions"]

        # 3. Construct 7 correct answers and 3 wrong answers using independent mapping
        answers = []
        for idx, q in enumerate(questions):
            p_id = q["problem_id"]
            if idx < 7:
                answers.append({"problem_id": p_id, "selected_answer": problem_id_to_correct_opt[p_id]})
            else:
                answers.append({"problem_id": p_id, "selected_answer": "WRONG_ANSWER"})

        sub_resp = await ac.post(
            f"/api/v1/diagnostic/{ass_id}/submit",
            headers=get_auth_header(USER1_ID),
            json={"answers": answers},
        )

    assert sub_resp.status_code == 200
    res = sub_resp.json()
    assert res["status"] == "COMPLETED"
    assert res["total_questions"] == 10
    assert res["answered_questions"] == 10
    assert res["correct_answers"] == 7
    assert res["score"] == 70.0


@pytest.mark.asyncio
async def test_11_completed_assessment_cannot_be_submitted_again():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        start_resp = await ac.post(
            "/api/v1/diagnostic/start",
            headers=get_auth_header(USER1_ID),
        )
        data = start_resp.json()
        ass_id = data["assessment_id"]
        questions = data["questions"]

        answers = [{"problem_id": q["problem_id"], "selected_answer": "A"} for q in questions]

        await ac.post(
            f"/api/v1/diagnostic/{ass_id}/submit",
            headers=get_auth_header(USER1_ID),
            json={"answers": answers},
        )

        res2 = await ac.post(
            f"/api/v1/diagnostic/{ass_id}/submit",
            headers=get_auth_header(USER1_ID),
            json={"answers": answers},
        )
    assert res2.status_code == 400
    assert "already completed" in res2.json()["detail"]


@pytest.mark.asyncio
async def test_12_another_user_cannot_submit_someone_elses_assessment():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        start_resp = await ac.post(
            "/api/v1/diagnostic/start",
            headers=get_auth_header(USER1_ID),
        )
        data = start_resp.json()
        ass_id = data["assessment_id"]
        questions = data["questions"]

        answers = [{"problem_id": q["problem_id"], "selected_answer": "A"} for q in questions]

        sub_resp = await ac.post(
            f"/api/v1/diagnostic/{ass_id}/submit",
            headers=get_auth_header(USER2_ID),
            json={"answers": answers},
        )
    assert sub_resp.status_code == 403


@pytest.mark.asyncio
async def test_13_invalid_question_ids_are_rejected():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        start_resp = await ac.post(
            "/api/v1/diagnostic/start",
            headers=get_auth_header(USER1_ID),
        )
        ass_id = start_resp.json()["assessment_id"]

        invalid_answers = [{"problem_id": 88888, "selected_answer": "A"}]

        sub_resp = await ac.post(
            f"/api/v1/diagnostic/{ass_id}/submit",
            headers=get_auth_header(USER1_ID),
            json={"answers": invalid_answers},
        )
    assert sub_resp.status_code == 400


@pytest.mark.asyncio
async def test_14_diagnostic_questions_have_exactly_one_correct_answer_in_seed():
    async with TestSessionLocal() as session:
        stmt = select(Problem).where(Problem.is_diagnostic == True)
        diag_probs = (await session.execute(stmt)).scalars().all()

        assert len(diag_probs) == 10
        for p in diag_probs:
            assert p.is_diagnostic is True
            assert p.diagnostic_options is not None
            assert len(p.diagnostic_options) == 4
            assert p.diagnostic_correct_option is not None
            # Verify correct option matches one of the option prefixes
            corr = p.diagnostic_correct_option.strip().upper()
            prefixes = [opt.split('.')[0].strip().upper() for opt in p.diagnostic_options]
            assert corr in prefixes
