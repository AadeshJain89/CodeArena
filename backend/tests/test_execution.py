import pytest
import pytest_asyncio
import docker
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool

from sqlalchemy import select
from app.main import app
from app.core.config import settings
from app.core.db import get_db
from app.core.security import create_access_token, hash_password
from app.models.user import User, UserRole
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


TEST_USER_ID = None

@pytest_asyncio.fixture(autouse=True, scope="function")
async def ensure_seeded_db():
    global TEST_USER_ID
    async with TestSessionLocal() as session:
        await seed_data(session=session)
        
        # Ensure a test user exists in DB
        result = await session.execute(select(User).where(User.username == "exec_test_user"))
        user = result.scalar_one_or_none()
        if not user:
            user = User(
                username="exec_test_user",
                email="exectest@example.com",
                password_hash=hash_password("Password123!"),
                role=UserRole.USER,
                is_active=True,
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
        TEST_USER_ID = user.id


def get_auth_header():
    token = create_access_token(subject=str(TEST_USER_ID), role="USER")
    return {"Authorization": f"Bearer {token}"}



@pytest.mark.asyncio
async def test_1_authenticated_user_can_execute_code():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/execute",
            headers=get_auth_header(),
            json={
                "problem_id": 1,
                "language": "python",
                "source_code": "nums = [int(x) for x in input().split()]\nprint(max(nums))\n",
            },
        )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "PASSED"
    assert data["passed_tests"] == data["total_tests"]


@pytest.mark.asyncio
async def test_2_unauthenticated_request_rejected():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/execute",
            json={
                "problem_id": 1,
                "language": "python",
                "source_code": "print('hello')",
            },
        )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_3_nonexistent_problem_rejected():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/execute",
            headers=get_auth_header(),
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
            "/api/v1/execute",
            headers=get_auth_header(),
            json={
                "problem_id": 1,
                "language": "java",
                "source_code": "public class Solution {}",
            },
        )
    assert response.status_code == 400
    assert "Unsupported language" in response.json()["detail"]


@pytest.mark.asyncio
async def test_5_correct_python_solution_passes():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/execute",
            headers=get_auth_header(),
            json={
                "problem_id": 1,  # Find Maximum Element
                "language": "python",
                "source_code": "nums = [int(x) for x in input().split()]\nprint(max(nums))\n",
            },
        )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "PASSED"
    assert data["passed_tests"] > 0
    assert data["failed_tests"] == 0


@pytest.mark.asyncio
async def test_6_incorrect_python_solution_fails():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/execute",
            headers=get_auth_header(),
            json={
                "problem_id": 1,
                "language": "python",
                "source_code": "print(-999999)\n",
            },
        )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "FAILED"
    assert data["failed_tests"] > 0


@pytest.mark.asyncio
async def test_7_runtime_error_handled():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/execute",
            headers=get_auth_header(),
            json={
                "problem_id": 1,
                "language": "python",
                "source_code": "x = 1 / 0\n",
            },
        )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "RUNTIME_ERROR"
    assert "ZeroDivisionError" in data["test_results"][0]["error_message"]


@pytest.mark.asyncio
async def test_8_infinite_loop_times_out():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/execute",
            headers=get_auth_header(),
            json={
                "problem_id": 1,
                "language": "python",
                "source_code": "while True:\n    pass\n",
            },
        )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "TIME_LIMIT_EXCEEDED"


@pytest.mark.asyncio
async def test_9_output_size_limit_handled():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/execute",
            headers=get_auth_header(),
            json={
                "problem_id": 1,
                "language": "python",
                "source_code": "print('A' * 1000000)\n",
            },
        )
    assert response.status_code == 200
    data = response.json()
    # Output should be truncated or handled
    assert data["total_tests"] > 0


@pytest.mark.asyncio
async def test_10_hidden_test_inputs_never_returned():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/execute",
            headers=get_auth_header(),
            json={
                "problem_id": 1,
                "language": "python",
                "source_code": "def solve(nums):\n    return max(nums)\n",
            },
        )
    assert response.status_code == 200
    data = response.json()
    for res in data["test_results"]:
        if res["is_hidden"]:
            assert res["actual_output"] is None
            assert res["expected_output"] is None


@pytest.mark.asyncio
async def test_11_container_cleaned_up():
    client = docker.from_env()
    before_containers = client.containers.list(all=True)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        await ac.post(
            "/api/v1/execute",
            headers=get_auth_header(),
            json={
                "problem_id": 1,
                "language": "python",
                "source_code": "print(42)\n",
            },
        )

    after_containers = client.containers.list(all=True)
    # Ensure no lingering execution container left behind
    assert len(after_containers) == len(before_containers)


@pytest.mark.asyncio
async def test_12_network_isolation_verified():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/execute",
            headers=get_auth_header(),
            json={
                "problem_id": 1,
                "language": "python",
                "source_code": "import socket\ns = socket.socket()\ns.settimeout(1)\ns.connect(('8.8.8.8', 53))\n",
            },
        )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "RUNTIME_ERROR"
    err = data["test_results"][0]["error_message"]
    assert "OSError" in err or "Network is unreachable" in err or "TimeoutError" in err or "socket" in err


@pytest.mark.asyncio
async def test_13_environment_isolation_verified():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/execute",
            headers=get_auth_header(),
            json={
                "problem_id": 1,
                "language": "python",
                "source_code": "import os\nprint(os.environ.get('POSTGRES_PASSWORD', ''))\n",
            },
        )
    assert response.status_code == 200
    data = response.json()
    # Output should not contain host postgres password
    for res in data["test_results"]:
        if not res["is_hidden"]:
            assert "codearena_password" not in res.get("actual_output", "")


@pytest.mark.asyncio
async def test_14_source_code_size_limit_works():
    huge_code = "# " + ("A" * (settings.CODE_EXECUTION_MAX_SOURCE_BYTES + 100))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/execute",
            headers=get_auth_header(),
            json={
                "problem_id": 1,
                "language": "python",
                "source_code": huge_code,
            },
        )
    assert response.status_code == 400
    assert "exceeds maximum limit" in response.json()["detail"]


@pytest.mark.asyncio
async def test_15_cpp_execution_passes():
    cpp_code = """#include <iostream>
#include <algorithm>
#include <vector>
using namespace std;

int main() {
    int val, mx = -999999;
    while (cin >> val) {
        if (val > mx) mx = val;
    }
    cout << mx << endl;
    return 0;
}
"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/execute",
            headers=get_auth_header(),
            json={
                "problem_id": 1,
                "language": "cpp",
                "source_code": cpp_code,
            },
        )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "PASSED"
    assert data["passed_tests"] > 0


@pytest.mark.asyncio
async def test_16_solve_function_single_element_list_input_passes():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/execute",
            headers=get_auth_header(),
            json={
                "problem_id": 1,
                "language": "python",
                "source_code": "def solve(nums: list[int]) -> int:\n    return max(nums)\n",
            },
        )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "PASSED"
    assert data["passed_tests"] == data["total_tests"]
    assert data["failed_tests"] == 0
    # Ensure test case 3 (input "42") passed
    hidden_tcs = [tc for tc in data["test_results"] if tc["is_hidden"]]
    assert len(hidden_tcs) >= 2
    for tc in hidden_tcs:
        assert tc["status"] == "PASSED"


@pytest.mark.asyncio
async def test_17_solve_function_multi_element_list_input_passes():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/execute",
            headers=get_auth_header(),
            json={
                "problem_id": 1,
                "language": "python",
                "source_code": "def solve(nums: list[int]) -> int:\n    return max(nums)\n",
            },
        )
    assert response.status_code == 200
    data = response.json()
    # Check test case 1 (input "1 5 3 9 2")
    tc1 = [tc for tc in data["test_results"] if tc["test_number"] == 1][0]
    assert tc1["status"] == "PASSED"
    assert tc1["actual_output"] == "9"
    assert tc1["expected_output"] == "9"
