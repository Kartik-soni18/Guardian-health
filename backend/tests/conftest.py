"""Pytest fixtures — mongomock users + mock-mode LangGraph."""

import asyncio
import os
from typing import Any, AsyncGenerator, Dict, Generator

os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault(
    "SECRET_KEY",
    "test-secret-key-with-at-least-32-characters-long",
)
os.environ.setdefault("MOCK_MODE", "true")

import mongomock
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.config import get_settings
from app.core.dependencies import get_mongodb_manager
from app.core.security import create_token_pair, get_password_hash
from app.db.mongodb import MongoDBManager
from app.graph import reset_graph
from app.main import create_app
from app.services.triage_service import TriageService


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def test_settings(monkeypatch: pytest.MonkeyPatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "secret_key", os.environ["SECRET_KEY"])
    monkeypatch.setattr(settings, "mock_mode", True)
    monkeypatch.setattr(settings, "guardian_env", "test")
    monkeypatch.setattr(settings, "debug", True)
    return settings


@pytest_asyncio.fixture(scope="function")
async def test_db(test_settings) -> AsyncGenerator[MongoDBManager, None]:
    client = mongomock.MongoClient()
    sync_db = client["test_guardian"]
    yield MongoDBManager(sync_db=sync_db)


@pytest_asyncio.fixture(scope="function")
async def test_user(test_db: MongoDBManager) -> Dict[str, Any]:
    return await test_db.create_user({
        "username": "testuser",
        "password_hash": get_password_hash("TestPass123!"),
    })


@pytest.fixture(scope="function")
def auth_headers(test_user: Dict[str, Any]) -> Dict[str, str]:
    access_token, _ = create_token_pair(
        test_user["username"],
        extra_claims={"uid": test_user["id"]},
    )
    return {"Authorization": f"Bearer {access_token}"}


@pytest_asyncio.fixture(scope="function")
async def test_app(
    test_db: MongoDBManager,
    test_settings,
    monkeypatch: pytest.MonkeyPatch,
) -> AsyncGenerator[AsyncClient, None]:
    reset_graph()
    TriageService.reset()

    async def _noop_connect() -> None:
        return None

    async def _noop_close() -> None:
        return None

    async def _ping_ok() -> bool:
        return True

    monkeypatch.setattr("app.db.mongodb.connect_mongodb", _noop_connect)
    monkeypatch.setattr("app.db.mongodb.ensure_mongodb", _noop_connect)
    monkeypatch.setattr("app.db.mongodb.close_mongodb", _noop_close)
    monkeypatch.setattr("app.db.mongodb.ping_mongodb", _ping_ok)

    app = create_app()
    app.dependency_overrides[get_mongodb_manager] = lambda: test_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()
    reset_graph()


@pytest.fixture(autouse=True)
def reset_rate_limits():
    from app.core.dependencies import limiter
    try:
        limiter._storage.reset()
    except Exception:
        pass
