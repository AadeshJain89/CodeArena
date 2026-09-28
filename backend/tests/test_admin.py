import uuid
from datetime import datetime, timezone
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
from app.models.problem import Problem, ProblemDifficulty
from app.models.topic import Topic
from app.models.test_case import TestCase
from app.models.submission import Submission
from app.models.submission_test_result import SubmissionTestResult
from app.models.diagnostic_response import DiagnosticResponse
from app.models.diagnostic_assessment import DiagnosticAssessment
from app.models.diagnostic_assessment_question import DiagnosticAssessmentQuestion
from app.models.recommendation import Recommendation
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


@pytest_asyncio.fixture(autouse=True, scope="function")
async def ensure_seeded_db():
    async with TestSessionLocal() as session:
        await seed_data(session=session)


async def create_test_user(prefix: str = "user", role: UserRole = UserRole.USER) -> int:
    unique_str = uuid.uuid4().hex[:8]
    async with TestSessionLocal() as session:
        u = User(
            username=f"{prefix}_{unique_str}",
            email=f"{prefix}_{unique_str}@example.com",
            password_hash=hash_password("Password123!"),
            role=role,
            is_active=True,
        )
        session.add(u)
        await session.commit()
        await session.refresh(u)
        return u.id


def get_auth_header(user_id: int, role: str = "USER"):
    token = create_access_token(subject=str(user_id), role=role)
    return {"Authorization": f"Bearer {token}"}


# ==================================================
# 1. AUTHORIZATION TESTS
# ==================================================

@pytest.mark.asyncio
async def test_1_unauthenticated_admin_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/admin/problems")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_2_normal_user_rejected():
    user_id = await create_test_user("normal_user", UserRole.USER)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/admin/problems", headers=get_auth_header(user_id, "USER"))
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_3_admin_user_allowed():
    admin_id = await create_test_user("admin_user", UserRole.ADMIN)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/admin/problems", headers=get_auth_header(admin_id, "ADMIN"))
    assert res.status_code == 200


# ==================================================
# 2. PROBLEM CRUD TESTS
# ==================================================

@pytest.mark.asyncio
async def test_4_admin_can_list_problems():
    admin_id = await create_test_user("admin_list", UserRole.ADMIN)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/admin/problems", headers=get_auth_header(admin_id, "ADMIN"))
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] > 0


@pytest.mark.asyncio
async def test_5_admin_can_create_problem():
    admin_id = await create_test_user("admin_create", UserRole.ADMIN)
    unique_title = f"Admin Unique Challenge {uuid.uuid4().hex[:8]}"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {
            "title": unique_title,
            "description": "Write a program to solve this.",
            "difficulty": "EASY",
            "topic_ids": [1, 2],
        }
        res = await ac.post("/api/v1/admin/problems", json=payload, headers=get_auth_header(admin_id, "ADMIN"))
    assert res.status_code == 201
    data = res.json()
    assert data["title"] == unique_title
    assert len(data["topics"]) == 2

    # Clean up temp problem
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        await ac.delete(f"/api/v1/admin/problems/{data['id']}", headers=get_auth_header(admin_id, "ADMIN"))


@pytest.mark.asyncio
async def test_6_admin_can_retrieve_problem():
    admin_id = await create_test_user("admin_get", UserRole.ADMIN)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/admin/problems/1", headers=get_auth_header(admin_id, "ADMIN"))
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == 1
    assert "test_cases" in data


@pytest.mark.asyncio
async def test_7_admin_can_update_problem():
    admin_id = await create_test_user("admin_update", UserRole.ADMIN)
    unique_str = uuid.uuid4().hex[:8]
    async with TestSessionLocal() as db:
        p = Problem(
            title=f"Temp Problem For Update {unique_str}",
            slug=f"temp-problem-for-update-{unique_str}",
            description="desc",
            difficulty=ProblemDifficulty.EASY,
        )
        db.add(p)
        await db.commit()
        await db.refresh(p)
        temp_id = p.id

    unique_title = f"Updated Title {unique_str}"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {
            "title": unique_title,
            "difficulty": "HARD",
            "topic_ids": [3],
        }
        res = await ac.put(f"/api/v1/admin/problems/{temp_id}", json=payload, headers=get_auth_header(admin_id, "ADMIN"))
    assert res.status_code == 200
    data = res.json()
    assert data["title"] == unique_title
    assert data["difficulty"] == "HARD"
    assert len(data["topics"]) == 1
    assert data["topics"][0]["id"] == 3

    # Clean up temp problem
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        await ac.delete(f"/api/v1/admin/problems/{temp_id}", headers=get_auth_header(admin_id, "ADMIN"))


@pytest.mark.asyncio
async def test_8_admin_can_delete_unused_problem():
    """A brand-new problem with no historical records can be deleted."""
    admin_id = await create_test_user("admin_del", UserRole.ADMIN)
    unique_str = uuid.uuid4().hex[:8]
    # Create temp problem with no FK dependents
    async with TestSessionLocal() as db:
        p = Problem(
            title=f"Temp Problem To Delete {unique_str}",
            slug=f"temp-problem-to-delete-{unique_str}",
            description="desc",
            difficulty=ProblemDifficulty.EASY,
        )
        db.add(p)
        await db.commit()
        await db.refresh(p)
        temp_id = p.id

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.delete(f"/api/v1/admin/problems/{temp_id}", headers=get_auth_header(admin_id, "ADMIN"))
    assert res.status_code == 200
    assert "deleted successfully" in res.json()["message"]

    # Verify deleted
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res_check = await ac.get(f"/api/v1/admin/problems/{temp_id}", headers=get_auth_header(admin_id, "ADMIN"))
    assert res_check.status_code == 404


@pytest.mark.asyncio
async def test_8b_delete_problem_with_submission_is_rejected():
    """Deleting a problem that has submissions returns HTTP 409 Conflict."""
    admin_id = await create_test_user("admin_del_sub", UserRole.ADMIN)
    user_id = await create_test_user("user_del_sub", UserRole.USER)
    unique_str = uuid.uuid4().hex[:8]

    # Create an isolated temp problem
    async with TestSessionLocal() as db:
        p = Problem(
            title=f"Protected Problem Sub {unique_str}",
            slug=f"protected-problem-sub-{unique_str}",
            description="desc",
            difficulty=ProblemDifficulty.EASY,
        )
        db.add(p)
        await db.flush()

        # Create a submission referencing this problem
        sub = Submission(
            user_id=user_id,
            problem_id=p.id,
            language="PYTHON",
            source_code="print('ok')",
            status="PASSED",
            total_tests=1,
            passed_tests=1,
            failed_tests=0,
            created_at=datetime.now(timezone.utc),
        )
        db.add(sub)
        await db.commit()
        await db.refresh(sub)
        temp_prob_id = p.id
        temp_sub_id = sub.id

    # Attempt deletion — must fail with 409
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.delete(
            f"/api/v1/admin/problems/{temp_prob_id}",
            headers=get_auth_header(admin_id, "ADMIN"),
        )
    assert res.status_code == 409
    detail = res.json()["detail"]
    assert "submission" in detail.lower() or "historical" in detail.lower()

    # Verify the problem still exists
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res_check = await ac.get(
            f"/api/v1/admin/problems/{temp_prob_id}",
            headers=get_auth_header(admin_id, "ADMIN"),
        )
    assert res_check.status_code == 200

    # Verify the submission still exists in DB
    async with TestSessionLocal() as db:
        sub_record = await db.get(Submission, temp_sub_id)
        assert sub_record is not None, "Submission must be preserved after rejected deletion"
        assert sub_record.problem_id == temp_prob_id

    # --- Teardown: remove submission first, then the problem is safe to delete ---
    async with TestSessionLocal() as db:
        sub_rec = await db.get(Submission, temp_sub_id)
        if sub_rec:
            await db.delete(sub_rec)
            await db.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        cleanup = await ac.delete(
            f"/api/v1/admin/problems/{temp_prob_id}",
            headers=get_auth_header(admin_id, "ADMIN"),
        )
    assert cleanup.status_code == 200


@pytest.mark.asyncio
async def test_8c_delete_problem_with_diagnostic_response_is_rejected():
    """Deleting a problem that has DiagnosticResponse records returns HTTP 409 Conflict."""
    admin_id = await create_test_user("admin_del_diag", UserRole.ADMIN)
    user_id = await create_test_user("user_del_diag", UserRole.USER)
    unique_str = uuid.uuid4().hex[:8]

    async with TestSessionLocal() as db:
        # Create an isolated temp problem
        p = Problem(
            title=f"Protected Problem Diag {unique_str}",
            slug=f"protected-problem-diag-{unique_str}",
            description="desc",
            difficulty=ProblemDifficulty.EASY,
        )
        db.add(p)
        await db.flush()

        # Create a diagnostic assessment to satisfy the FK on DiagnosticAssessmentQuestion
        assessment = DiagnosticAssessment(
            user_id=user_id,
            status="COMPLETED",
        )
        db.add(assessment)
        await db.flush()

        # Create a DiagnosticResponse referencing this problem
        diag_resp = DiagnosticResponse(
            assessment_id=assessment.id,
            problem_id=p.id,
            selected_answer="A",
            is_correct=True,
        )
        db.add(diag_resp)
        await db.commit()
        await db.refresh(diag_resp)
        temp_prob_id = p.id
        temp_diag_resp_id = diag_resp.id

    # Attempt deletion — must fail with 409
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.delete(
            f"/api/v1/admin/problems/{temp_prob_id}",
            headers=get_auth_header(admin_id, "ADMIN"),
        )
    assert res.status_code == 409
    detail = res.json()["detail"]
    assert "diagnostic" in detail.lower()

    # Verify DiagnosticResponse still exists
    async with TestSessionLocal() as db:
        dr = await db.get(DiagnosticResponse, temp_diag_resp_id)
        assert dr is not None, "DiagnosticResponse must be preserved after rejected deletion"
        assert dr.problem_id == temp_prob_id

    # --- Teardown: remove DiagnosticResponse (cascades via assessment delete), then problem ---
    # Deleting the assessment cascades to its responses via 'cascade="all, delete-orphan"'
    async with TestSessionLocal() as db:
        dr_rec = await db.get(DiagnosticResponse, temp_diag_resp_id)
        if dr_rec:
            await db.delete(dr_rec)
            await db.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        cleanup = await ac.delete(
            f"/api/v1/admin/problems/{temp_prob_id}",
            headers=get_auth_header(admin_id, "ADMIN"),
        )
    assert cleanup.status_code == 200


@pytest.mark.asyncio
async def test_9_invalid_problem_data_rejected():
    admin_id = await create_test_user("admin_inv", UserRole.ADMIN)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {
            "title": "",  # Invalid title
        }
        res = await ac.post("/api/v1/admin/problems", json=payload, headers=get_auth_header(admin_id, "ADMIN"))
    assert res.status_code == 422  # Pydantic validation error


@pytest.mark.asyncio
async def test_10_invalid_topic_association_rejected():
    admin_id = await create_test_user("admin_inv_topic", UserRole.ADMIN)
    unique_title = f"Invalid Topic Challenge {uuid.uuid4().hex[:8]}"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {
            "title": unique_title,
            "description": "desc",
            "difficulty": "EASY",
            "topic_ids": [999999],  # Non-existent topic ID
        }
        res = await ac.post("/api/v1/admin/problems", json=payload, headers=get_auth_header(admin_id, "ADMIN"))
    assert res.status_code == 400
    assert "topic_ids do not exist" in res.json()["detail"]


@pytest.mark.asyncio
async def test_11_duplicate_topic_association_prevented():
    admin_id = await create_test_user("admin_dup_topic", UserRole.ADMIN)
    unique_title = f"Duplicate Topic Challenge {uuid.uuid4().hex[:8]}"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {
            "title": unique_title,
            "description": "desc",
            "difficulty": "EASY",
            "topic_ids": [1, 1, 1],  # Duplicate topic IDs
        }
        res = await ac.post("/api/v1/admin/problems", json=payload, headers=get_auth_header(admin_id, "ADMIN"))
    assert res.status_code == 201
    data = res.json()
    assert len(data["topics"]) == 1

    # Clean up temp problem
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        await ac.delete(f"/api/v1/admin/problems/{data['id']}", headers=get_auth_header(admin_id, "ADMIN"))


# ==================================================
# 3. TEST CASE CRUD TESTS
# ==================================================

@pytest.mark.asyncio
async def test_12_admin_can_create_test_case():
    admin_id = await create_test_user("admin_tc_create", UserRole.ADMIN)
    unique_str = uuid.uuid4().hex[:8]
    async with TestSessionLocal() as db:
        p = Problem(
            title=f"Temp Problem TC Create {unique_str}",
            slug=f"temp-problem-tc-create-{unique_str}",
            description="desc",
            difficulty=ProblemDifficulty.EASY,
        )
        db.add(p)
        await db.commit()
        await db.refresh(p)
        temp_id = p.id

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {
            "input": "5 10\n",
            "expected_output": "15\n",
            "is_hidden": True,
        }
        res = await ac.post(f"/api/v1/admin/problems/{temp_id}/test-cases", json=payload, headers=get_auth_header(admin_id, "ADMIN"))
    assert res.status_code == 201
    data = res.json()
    assert data["problem_id"] == temp_id
    assert data["input"] == "5 10\n"
    assert data["is_hidden"] is True

    # Clean up temp problem
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        await ac.delete(f"/api/v1/admin/problems/{temp_id}", headers=get_auth_header(admin_id, "ADMIN"))


@pytest.mark.asyncio
async def test_13_admin_can_list_test_cases():
    admin_id = await create_test_user("admin_tc_list", UserRole.ADMIN)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/admin/problems/1/test-cases", headers=get_auth_header(admin_id, "ADMIN"))
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) > 0


@pytest.mark.asyncio
async def test_14_admin_can_retrieve_test_case():
    admin_id = await create_test_user("admin_tc_get", UserRole.ADMIN)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/admin/test-cases/1", headers=get_auth_header(admin_id, "ADMIN"))
    assert res.status_code == 200
    data = res.json()
    assert data["test_case_id"] == 1


@pytest.mark.asyncio
async def test_15_admin_can_update_test_case():
    admin_id = await create_test_user("admin_tc_upd", UserRole.ADMIN)
    unique_str = uuid.uuid4().hex[:8]
    async with TestSessionLocal() as db:
        p = Problem(
            title=f"Temp Problem TC Update {unique_str}",
            slug=f"temp-problem-tc-update-{unique_str}",
            description="desc",
            difficulty=ProblemDifficulty.EASY,
        )
        db.add(p)
        await db.flush()
        tc = TestCase(
            problem_id=p.id,
            input="in",
            expected_output="out",
            is_hidden=True,
        )
        db.add(tc)
        await db.commit()
        await db.refresh(tc)
        temp_tc_id = tc.test_case_id
        temp_p_id = p.id

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {
            "expected_output": "Updated Expected\n",
            "is_hidden": False,
        }
        res = await ac.put(f"/api/v1/admin/test-cases/{temp_tc_id}", json=payload, headers=get_auth_header(admin_id, "ADMIN"))
    assert res.status_code == 200
    data = res.json()
    assert data["expected_output"] == "Updated Expected\n"
    assert data["is_hidden"] is False

    # Clean up temp problem
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        await ac.delete(f"/api/v1/admin/problems/{temp_p_id}", headers=get_auth_header(admin_id, "ADMIN"))


@pytest.mark.asyncio
async def test_16_admin_can_delete_test_case():
    admin_id = await create_test_user("admin_tc_del", UserRole.ADMIN)
    # Create temp test case
    async with TestSessionLocal() as db:
        tc = TestCase(
            problem_id=1,
            input="in",
            expected_output="out",
            is_hidden=False,
        )
        db.add(tc)
        await db.commit()
        await db.refresh(tc)
        tc_id = tc.test_case_id

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.delete(f"/api/v1/admin/test-cases/{tc_id}", headers=get_auth_header(admin_id, "ADMIN"))
    assert res.status_code == 200

    # Verify deleted
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res_check = await ac.get(f"/api/v1/admin/test-cases/{tc_id}", headers=get_auth_header(admin_id, "ADMIN"))
    assert res_check.status_code == 404


@pytest.mark.asyncio
async def test_17_normal_user_cannot_access_admin_test_cases():
    user_id = await create_test_user("norm_user_tc", UserRole.USER)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res1 = await ac.get("/api/v1/admin/problems/1/test-cases", headers=get_auth_header(user_id, "USER"))
        res2 = await ac.get("/api/v1/admin/test-cases/1", headers=get_auth_header(user_id, "USER"))
    assert res1.status_code == 403
    assert res2.status_code == 403


@pytest.mark.asyncio
async def test_18_hidden_test_case_remains_hidden_from_normal_problem_apis():
    # Verify public problem API hides hidden test cases
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/problems/1")
    assert res.status_code == 200
    data = res.json()
    public_cases = data["public_test_cases"]
    # Check no hidden test case expected output leaked in public_test_cases
    for tc in public_cases:
        assert tc.get("is_hidden") is None or tc.get("is_hidden") is False


@pytest.mark.asyncio
async def test_19_problem_update_integrity_with_submissions():
    """Updating a problem title/metadata does NOT corrupt existing submissions."""
    admin_id = await create_test_user("admin_integrity", UserRole.ADMIN)
    user_id = await create_test_user("user_sub", UserRole.USER)

    unique_title = f"Integrity Challenge {uuid.uuid4().hex[:8]}"

    # Create problem
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        p_res = await ac.post(
            "/api/v1/admin/problems",
            json={
                "title": unique_title,
                "description": "desc",
                "difficulty": "EASY",
            },
            headers=get_auth_header(admin_id, "ADMIN"),
        )
    prob_id = p_res.json()["id"]

    # Submit to this problem
    async with TestSessionLocal() as db:
        sub = Submission(
            user_id=user_id,
            problem_id=prob_id,
            language="PYTHON",
            source_code="print('ok')",
            status="PASSED",
            total_tests=1,
            passed_tests=1,
            failed_tests=0,
            created_at=datetime.now(timezone.utc),
        )
        db.add(sub)
        await db.commit()
        await db.refresh(sub)
        sub_id = sub.id

    # Admin updates problem title — must succeed and NOT affect submissions
    updated_title = f"Updated Integrity {uuid.uuid4().hex[:8]}"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        u_res = await ac.put(
            f"/api/v1/admin/problems/{prob_id}",
            json={"title": updated_title},
            headers=get_auth_header(admin_id, "ADMIN"),
        )
    assert u_res.status_code == 200
    assert u_res.json()["title"] == updated_title

    # Verify submission remains intact after update
    async with TestSessionLocal() as db:
        sub_record = await db.get(Submission, sub_id)
        assert sub_record is not None
        assert sub_record.problem_id == prob_id

    # Attempting to delete the problem with submissions MUST return 409
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        del_res = await ac.delete(
            f"/api/v1/admin/problems/{prob_id}",
            headers=get_auth_header(admin_id, "ADMIN"),
        )
    assert del_res.status_code == 409
    assert "submission" in del_res.json()["detail"].lower()

    # Verify the problem and submission still exist
    async with TestSessionLocal() as db:
        sub_record2 = await db.get(Submission, sub_id)
        assert sub_record2 is not None, "Submission must NOT be deleted"

    # Teardown: remove submission first, then the problem (safe state)
    async with TestSessionLocal() as db:
        sub_rec = await db.get(Submission, sub_id)
        if sub_rec:
            await db.delete(sub_rec)
            await db.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        cleanup_res = await ac.delete(
            f"/api/v1/admin/problems/{prob_id}",
            headers=get_auth_header(admin_id, "ADMIN"),
        )
    assert cleanup_res.status_code == 200
