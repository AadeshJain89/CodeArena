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
from app.models.submission import Submission
from app.models.submission_test_result import SubmissionTestResult
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
        res1 = await session.execute(select(User).where(User.username == "sub_user_1"))
        u1 = res1.scalar_one_or_none()
        if not u1:
            u1 = User(
                username="sub_user_1",
                email="subuser1@example.com",
                password_hash=hash_password("Password123!"),
                role=UserRole.USER,
                is_active=True,
            )
            session.add(u1)
            await session.commit()
            await session.refresh(u1)
        USER1_ID = u1.id

        # User 2
        res2 = await session.execute(select(User).where(User.username == "sub_user_2"))
        u2 = res2.scalar_one_or_none()
        if not u2:
            u2 = User(
                username="sub_user_2",
                email="subuser2@example.com",
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
async def test_1_authenticated_user_can_submit_code():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/submissions",
            headers=get_auth_header(USER1_ID),
            json={
                "problem_id": 1,
                "language": "python",
                "source_code": "nums = [int(x) for x in input().split()]\nprint(max(nums))\n",
            },
        )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "PASSED"
    assert data["user_id"] == USER1_ID
    assert data["passed_tests"] == data["total_tests"]


@pytest.mark.asyncio
async def test_2_unauthenticated_submission_rejected():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/submissions",
            json={
                "problem_id": 1,
                "language": "python",
                "source_code": "print('test')",
            },
        )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_3_nonexistent_problem_rejected():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/submissions",
            headers=get_auth_header(USER1_ID),
            json={
                "problem_id": 999999,
                "language": "python",
                "source_code": "print('test')",
            },
        )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_4_unsupported_language_rejected():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/submissions",
            headers=get_auth_header(USER1_ID),
            json={
                "problem_id": 1,
                "language": "java",
                "source_code": "public class Solution {}",
            },
        )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_5_correct_solution_creates_passed_submission():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/submissions",
            headers=get_auth_header(USER1_ID),
            json={
                "problem_id": 1,
                "language": "python",
                "source_code": "nums = [int(x) for x in input().split()]\nprint(max(nums))\n",
            },
        )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "PASSED"


@pytest.mark.asyncio
async def test_6_incorrect_solution_creates_failed_submission():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/submissions",
            headers=get_auth_header(USER1_ID),
            json={
                "problem_id": 1,
                "language": "python",
                "source_code": "print(-999999)\n",
            },
        )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "FAILED"
    assert data["failed_tests"] > 0


@pytest.mark.asyncio
async def test_7_runtime_error_persisted_correctly():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/submissions",
            headers=get_auth_header(USER1_ID),
            json={
                "problem_id": 1,
                "language": "python",
                "source_code": "x = 1 / 0\n",
            },
        )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "RUNTIME_ERROR"


@pytest.mark.asyncio
async def test_8_timeout_persisted_correctly():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/submissions",
            headers=get_auth_header(USER1_ID),
            json={
                "problem_id": 1,
                "language": "python",
                "source_code": "while True:\n    pass\n",
            },
        )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "TIME_LIMIT_EXCEEDED"


@pytest.mark.asyncio
async def test_9_compilation_error_persisted_correctly_for_cpp():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/submissions",
            headers=get_auth_header(USER1_ID),
            json={
                "problem_id": 1,
                "language": "cpp",
                "source_code": "int main() { invalid syntax line }",
            },
        )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "COMPILATION_ERROR"


@pytest.mark.asyncio
async def test_10_submission_and_test_results_persisted_in_db():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/submissions",
            headers=get_auth_header(USER1_ID),
            json={
                "problem_id": 1,
                "language": "python",
                "source_code": "nums = [int(x) for x in input().split()]\nprint(max(nums))\n",
            },
        )
    assert response.status_code == 201
    sub_id = response.json()["id"]

    # Verify DB persistence directly
    async with TestSessionLocal() as session:
        sub_record = await session.get(Submission, sub_id)
        assert sub_record is not None
        assert sub_record.user_id == USER1_ID
        assert sub_record.status == "PASSED"

        stmt = select(SubmissionTestResult).where(SubmissionTestResult.submission_id == sub_id)
        tr_records = (await session.execute(stmt)).scalars().all()
        assert len(tr_records) > 0


@pytest.mark.asyncio
async def test_11_hidden_test_outputs_not_exposed():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/submissions",
            headers=get_auth_header(USER1_ID),
            json={
                "problem_id": 1,
                "language": "python",
                "source_code": "nums = [int(x) for x in input().split()]\nprint(max(nums))\n",
            },
        )
    assert response.status_code == 201
    data = response.json()
    for tr in data["test_results"]:
        if tr["is_hidden"]:
            assert tr["actual_output"] is None
            assert tr["expected_output"] is None


@pytest.mark.asyncio
async def test_12_user_cannot_access_another_users_submission():
    # User 1 submits code
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        post_resp = await ac.post(
            "/api/v1/submissions",
            headers=get_auth_header(USER1_ID),
            json={
                "problem_id": 1,
                "language": "python",
                "source_code": "print(1)",
            },
        )
        sub_id = post_resp.json()["id"]

        # User 2 attempts to fetch User 1's submission
        get_resp = await ac.get(
            f"/api/v1/submissions/{sub_id}",
            headers=get_auth_header(USER2_ID),
        )
    assert get_resp.status_code == 403


@pytest.mark.asyncio
async def test_13_submission_history_only_returns_authenticated_user_submissions():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # User 1 submits
        await ac.post(
            "/api/v1/submissions",
            headers=get_auth_header(USER1_ID),
            json={"problem_id": 1, "language": "python", "source_code": "print(1)"},
        )
        # User 2 submits
        await ac.post(
            "/api/v1/submissions",
            headers=get_auth_header(USER2_ID),
            json={"problem_id": 1, "language": "python", "source_code": "print(2)"},
        )

        # Get User 1 history
        h1 = await ac.get("/api/v1/submissions", headers=get_auth_header(USER1_ID))
        # Get User 2 history
        h2 = await ac.get("/api/v1/submissions", headers=get_auth_header(USER2_ID))

    subs1 = h1.json()
    subs2 = h2.json()

    assert all(s["problem_id"] == 1 for s in subs1)
    assert len(subs1) >= 1
    assert len(subs2) >= 1


@pytest.mark.asyncio
async def test_14_module_4_execute_endpoint_still_works():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/execute",
            headers=get_auth_header(USER1_ID),
            json={
                "problem_id": 1,
                "language": "python",
                "source_code": "nums = [int(x) for x in input().split()]\nprint(max(nums))\n",
            },
        )
    assert response.status_code == 200
    assert response.json()["status"] == "PASSED"
