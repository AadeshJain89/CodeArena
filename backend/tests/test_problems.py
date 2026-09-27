import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool
from sqlalchemy import select, func

from app.main import app
from app.core.config import settings
from app.core.db import get_db
from app.models.topic import Topic
from app.models.problem import Problem, ProblemDifficulty
from app.models.test_case import TestCase
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
    """Ensure seed data is populated before tests."""
    async with TestSessionLocal() as session:
        await seed_data(session=session)



@pytest.mark.asyncio
async def test_1_topic_listing():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/topics")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 12
    topic_names = [t["name"] for t in data]
    assert "Arrays" in topic_names
    assert "Dynamic Programming" in topic_names


@pytest.mark.asyncio
async def test_2_topic_detail():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        topics_resp = await ac.get("/api/v1/topics")
        first_topic = topics_resp.json()[0]

        response = await ac.get(f"/api/v1/topics/{first_topic['id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == first_topic["id"]
    assert data["name"] == first_topic["name"]


@pytest.mark.asyncio
async def test_3_problem_listing():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/problems")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 36
    assert len(data["items"]) == 10  # default page_size
    assert "topics" in data["items"][0]


@pytest.mark.asyncio
async def test_4_problem_detail():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        problems_resp = await ac.get("/api/v1/problems")
        first_problem = problems_resp.json()["items"][0]

        response = await ac.get(f"/api/v1/problems/{first_problem['id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == first_problem["id"]
    assert data["title"] == first_problem["title"]
    assert "description" in data
    assert "constraints" in data


@pytest.mark.asyncio
async def test_5_difficulty_filtering():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/problems?difficulty=MEDIUM")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 12  # 12 MEDIUM problems
    for item in data["items"]:
        assert item["difficulty"] == "MEDIUM"


@pytest.mark.asyncio
async def test_6_topic_filtering():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/problems?topic=Arrays")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3  # 3 problems for Arrays
    for item in data["items"]:
        topic_names = [t["name"] for t in item["topics"]]
        assert "Arrays" in topic_names


@pytest.mark.asyncio
async def test_7_pagination():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response_p1 = await ac.get("/api/v1/problems?page=1&page_size=5")
        response_p2 = await ac.get("/api/v1/problems?page=2&page_size=5")

    assert response_p1.status_code == 200
    assert response_p2.status_code == 200

    p1_data = response_p1.json()
    p2_data = response_p2.json()

    assert p1_data["page"] == 1
    assert p1_data["page_size"] == 5
    assert len(p1_data["items"]) == 5

    assert p2_data["page"] == 2
    assert len(p2_data["items"]) == 5

    p1_ids = [item["id"] for item in p1_data["items"]]
    p2_ids = [item["id"] for item in p2_data["items"]]
    assert set(p1_ids).isdisjoint(set(p2_ids))


@pytest.mark.asyncio
async def test_8_invalid_problem_id():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/problems/999999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Problem with ID 999999 not found"


@pytest.mark.asyncio
async def test_9_hidden_test_cases_not_exposed():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        problems_resp = await ac.get("/api/v1/problems?page_size=1")
        problem_id = problems_resp.json()["items"][0]["id"]

        detail_resp = await ac.get(f"/api/v1/problems/{problem_id}")

    assert detail_resp.status_code == 200
    data = detail_resp.json()

    # Check that public_test_cases only contains non-hidden cases
    assert "public_test_cases" in data
    public_cases = data["public_test_cases"]

    # Direct query DB to get total test cases count including hidden
    async with TestSessionLocal() as session:
        db_tcs_stmt = select(TestCase).where(TestCase.problem_id == problem_id)
        db_tcs = (await session.execute(db_tcs_stmt)).scalars().all()
        hidden_tcs = [tc for tc in db_tcs if tc.is_hidden]

    assert len(hidden_tcs) > 0  # DB has hidden test cases
    assert len(public_cases) < len(db_tcs)  # API detail response filtered out hidden ones!


@pytest.mark.asyncio
async def test_10_seed_operation_idempotent():
    # Run seed_data again
    async with TestSessionLocal() as session:
        await seed_data(session=session)

    async with TestSessionLocal() as session:
        t_count = (await session.execute(select(func.count(Topic.id)))).scalar_one()
        p_count = (await session.execute(select(func.count(Problem.id)))).scalar_one()

    assert t_count == 12
    assert p_count == 36

