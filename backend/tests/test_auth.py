import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool
from sqlalchemy import select, delete

from app.main import app
from app.core.config import settings
from app.core.db import get_db
from app.models.user import User, UserRole
from app.core.security import hash_password, create_access_token

# Test engine with NullPool to prevent asyncpg event loop leakage
test_engine = create_async_engine(settings.ASYNC_DATABASE_URI, poolclass=NullPool, echo=False)
TestSessionLocal = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db():
    async with TestSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture(autouse=True)
async def cleanup_db():
    """Clean up test users in database before and after each test."""
    async with TestSessionLocal() as session:
        await session.execute(
            delete(User).where(User.username.in_(["testuser", "dupuser", "user1", "user2", "testadmin"]))
        )
        await session.commit()
    yield
    async with TestSessionLocal() as session:
        await session.execute(
            delete(User).where(User.username.in_(["testuser", "dupuser", "user1", "user2", "testadmin"]))
        )
        await session.commit()


@pytest.mark.asyncio
async def test_1_register_user_success():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/auth/register",
            json={
                "username": "testuser",
                "email": "testuser@example.com",
                "password": "Password123!",
            },
        )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "testuser@example.com"
    assert data["role"] == "USER"
    assert "password_hash" not in data


@pytest.mark.asyncio
async def test_2_duplicate_username_rejected():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        await ac.post(
            "/api/v1/auth/register",
            json={
                "username": "dupuser",
                "email": "dup1@example.com",
                "password": "Password123!",
            },
        )
        response = await ac.post(
            "/api/v1/auth/register",
            json={
                "username": "dupuser",
                "email": "dup2@example.com",
                "password": "Password123!",
            },
        )
    assert response.status_code == 409
    assert response.json()["detail"] == "Username is already taken"


@pytest.mark.asyncio
async def test_3_duplicate_email_rejected():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        await ac.post(
            "/api/v1/auth/register",
            json={
                "username": "user1",
                "email": "dupemail@example.com",
                "password": "Password123!",
            },
        )
        response = await ac.post(
            "/api/v1/auth/register",
            json={
                "username": "user2",
                "email": "dupemail@example.com",
                "password": "Password123!",
            },
        )
    assert response.status_code == 409
    assert response.json()["detail"] == "Email is already registered"


@pytest.mark.asyncio
async def test_4_login_success():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        await ac.post(
            "/api/v1/auth/register",
            json={
                "username": "testuser",
                "email": "testuser@example.com",
                "password": "Password123!",
            },
        )
        response = await ac.post(
            "/api/v1/auth/login",
            json={
                "login": "testuser",
                "password": "Password123!",
            },
        )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_5_login_incorrect_password_fails():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        await ac.post(
            "/api/v1/auth/register",
            json={
                "username": "testuser",
                "email": "testuser@example.com",
                "password": "Password123!",
            },
        )
        response = await ac.post(
            "/api/v1/auth/login",
            json={
                "login": "testuser",
                "password": "WrongPassword!",
            },
        )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


@pytest.mark.asyncio
async def test_6_auth_me_with_valid_jwt():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        reg_resp = await ac.post(
            "/api/v1/auth/register",
            json={
                "username": "testuser",
                "email": "testuser@example.com",
                "password": "Password123!",
            },
        )
        user_id = reg_resp.json()["id"]
        token = create_access_token(subject=str(user_id), role="USER")

        response = await ac.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "testuser@example.com"
    assert data["role"] == "USER"


@pytest.mark.asyncio
async def test_7_auth_me_without_jwt_fails():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_8_user_cannot_access_admin_test():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        reg_resp = await ac.post(
            "/api/v1/auth/register",
            json={
                "username": "testuser",
                "email": "testuser@example.com",
                "password": "Password123!",
            },
        )
        user_id = reg_resp.json()["id"]
        token = create_access_token(subject=str(user_id), role="USER")

        response = await ac.get(
            "/api/v1/admin/test",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert response.status_code == 403
    assert "Required role: ADMIN" in response.json()["detail"]


@pytest.mark.asyncio
async def test_9_admin_can_access_admin_test():
    async with TestSessionLocal() as session:
        admin = User(
            username="testadmin",
            email="admin@example.com",
            password_hash=hash_password("AdminPassword123!"),
            role=UserRole.ADMIN,
            is_active=True,
        )
        session.add(admin)
        await session.commit()
        await session.refresh(admin)
        admin_id = admin.id

    token = create_access_token(subject=str(admin_id), role="ADMIN")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get(
            "/api/v1/admin/test",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testadmin"
    assert data["role"] == "ADMIN"
