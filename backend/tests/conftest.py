import os
import sys
from pathlib import Path
from typing import AsyncGenerator
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Ensure backend directory is in python sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.core.config import settings
from app.db.database import Base, get_db
from app.main import app

# Use isolated test SQLite database
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_travel_agent.db"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

test_session_factory = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)
test_session_factory.__test__ = False


@pytest_asyncio.fixture(autouse=True)
async def setup_test_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with test_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


@pytest_asyncio.fixture
async def auth_headers(async_client: AsyncClient) -> dict:
    reg_resp = await async_client.post(
        "/api/auth/register",
        json={"email": "traveller@example.com", "password": "password123", "full_name": "Kanishka"}
    )
    login_resp = await async_client.post(
        "/api/auth/login",
        json={"email": "traveller@example.com", "password": "password123"}
    )
    token = login_resp.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def user_b_headers(async_client: AsyncClient) -> dict:
    await async_client.post(
        "/api/auth/register",
        json={"email": "user_b@example.com", "password": "password456", "full_name": "User B"}
    )
    login_resp = await async_client.post(
        "/api/auth/login",
        json={"email": "user_b@example.com", "password": "password456"}
    )
    token = login_resp.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}
