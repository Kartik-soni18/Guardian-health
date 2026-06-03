"""GuardianHealth v2 Pytest Configuration — Shared fixtures for all test modules."""


import asyncio
import os
import uuid
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Dict, Generator, List

import boto3
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from moto import mock_aws

from app.core.config import Settings, settings
from app.core.deps import get_dynamodb_manager, reset_dynamodb_manager
from app.core.security import create_token_pair, get_password_hash
from app.db.dynamodb import DynamoDBManager
from app.main import create_app
from app.services.health_service import HealthService

# ---------------------------------------------------------------------------
# Force test environment
# ---------------------------------------------------------------------------
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("SECRET_KEY", "test-secret-key-do-not-use-in-production")
os.environ.setdefault("DYNAMODB_TABLE_PREFIX", "test_")
os.environ.setdefault("AWS_ACCESS_KEY_ID", "testing")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "testing")
os.environ.setdefault("AWS_REGION", "us-east-1")
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")


# ---------------------------------------------------------------------------
# Event loop policy
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ---------------------------------------------------------------------------
# Moto mock for DynamoDB
# ---------------------------------------------------------------------------
@pytest.fixture(scope="function")
def mock_dynamodb() -> Generator[mock_aws, None, None]:
    """Start moto mock for DynamoDB."""
    with mock_aws() as m:
        yield m


# ---------------------------------------------------------------------------
# Test settings override
# ---------------------------------------------------------------------------
@pytest.fixture(scope="function")
def test_settings(monkeypatch: pytest.MonkeyPatch) -> Settings:
    """Override settings for tests."""
    monkeypatch.setattr(settings, "DYNAMODB_TABLE_PREFIX", "test_")
    monkeypatch.setattr(settings, "DYNAMODB_ENDPOINT_URL", None)
    monkeypatch.setattr(settings, "SECRET_KEY", "test-secret-key")
    monkeypatch.setattr(settings, "ACCESS_TOKEN_EXPIRE_MINUTES", 15)
    monkeypatch.setattr(settings, "REFRESH_TOKEN_EXPIRE_DAYS", 7)
    monkeypatch.setattr(settings, "ENVIRONMENT", "test")
    monkeypatch.setattr(settings, "DEBUG", True)
    return settings


# ---------------------------------------------------------------------------
# Create DynamoDB tables with "test_" prefix using synchronous boto3 (moto-friendly)
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture(scope="function")
async def test_tables(
    mock_dynamodb: mock_aws,
    test_settings: Settings,
) -> AsyncGenerator[DynamoDBManager, None]:
    """Create all DynamoDB tables with prefix 'test_' and yield manager."""
    users_name = "test_users"
    chats_name = "test_chats"

    # Use synchronous boto3 to create tables (moto works sync perfectly)
    resource = boto3.resource("dynamodb", region_name="us-east-1")

    # Users table
    resource.create_table(
        TableName=users_name,
        KeySchema=[{"AttributeName": "username", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "username", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )

    # Chats table with GSI
    resource.create_table(
        TableName=chats_name,
        KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
        AttributeDefinitions=[
            {"AttributeName": "id", "AttributeType": "S"},
            {"AttributeName": "user_id", "AttributeType": "S"},
        ],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "by_user",
                "KeySchema": [
                    {"AttributeName": "user_id", "KeyType": "HASH"},
                    {"AttributeName": "id", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            }
        ],
        BillingMode="PAY_PER_REQUEST",
    )

    # Async proxy for sync boto3 table (moto compatibility)
    class _AsyncTable:
        def __init__(self, sync_table):
            self._t = sync_table

        async def put_item(self, **kw):
            return self._t.put_item(**kw)

        async def get_item(self, **kw):
            return self._t.get_item(**kw)

        async def query(self, **kw):
            return self._t.query(**kw)

        async def scan(self, **kw):
            return self._t.scan(**kw)

        async def update_item(self, **kw):
            return self._t.update_item(**kw)

        async def delete_item(self, **kw):
            return self._t.delete_item(**kw)

    # Reset singleton and create fresh manager
    reset_dynamodb_manager()
    ddb = DynamoDBManager()

    # Manually set tables with async wrappers (bypass aioboto3 resource creation which can conflict with moto)
    ddb._resource = resource  # type: ignore[assignment]
    ddb._users_table = _AsyncTable(resource.Table(users_name))
    ddb._chats_table = _AsyncTable(resource.Table(chats_name))

    yield ddb

    # Cleanup
    reset_dynamodb_manager()


# ---------------------------------------------------------------------------
# Test user in mock DynamoDB
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture(scope="function")
async def test_user(test_tables: DynamoDBManager) -> Dict[str, Any]:
    """Create a test user in mock DynamoDB."""
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password_hash": get_password_hash("TestPass123!"),
        "full_name": "Test User",
    }
    user = await test_tables.create_user(user_data)
    return user


# ---------------------------------------------------------------------------
# Second test user (for ownership tests)
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture(scope="function")
async def other_user(test_tables: DynamoDBManager) -> Dict[str, Any]:
    """Create another test user for ownership tests."""
    user_data = {
        "username": "otheruser",
        "email": "other@example.com",
        "password_hash": get_password_hash("OtherPass123!"),
        "full_name": "Other User",
    }
    user = await test_tables.create_user(user_data)
    return user


# ---------------------------------------------------------------------------
# Test chat in mock DynamoDB
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture(scope="function")
async def test_chat(test_tables: DynamoDBManager, test_user: Dict[str, Any]) -> Dict[str, Any]:
    """Create a test chat owned by test_user."""
    messages = [
        {"role": "user", "content": "I have a headache", "timestamp": datetime.now(timezone.utc).isoformat()},
        {"role": "assistant", "content": "Let me help you", "timestamp": datetime.now(timezone.utc).isoformat()},
    ]
    chat = await test_tables.create_chat(
        user_id=test_user["id"],
        title="Headache Triage",
        messages=messages,
    )
    return chat


# ---------------------------------------------------------------------------
# Bearer token for test_user
# ---------------------------------------------------------------------------
@pytest.fixture(scope="function")
def auth_headers(test_user: Dict[str, Any]) -> Dict[str, str]:
    """Return Bearer token headers for test_user."""
    access_token, _ = create_token_pair(
        test_user["username"],
        extra_claims={"uid": test_user["id"]},
    )
    return {"Authorization": f"Bearer {access_token}"}


# ---------------------------------------------------------------------------
# Bearer token for other_user
# ---------------------------------------------------------------------------
@pytest.fixture(scope="function")
def other_auth_headers(other_user: Dict[str, Any]) -> Dict[str, str]:
    """Return Bearer token headers for other_user."""
    access_token, _ = create_token_pair(
        other_user["username"],
        extra_claims={"uid": other_user["id"]},
    )
    return {"Authorization": f"Bearer {access_token}"}


# ---------------------------------------------------------------------------
# Mock LLM client
# ---------------------------------------------------------------------------
@pytest.fixture(scope="function")
def mock_llm_client(monkeypatch: pytest.MonkeyPatch) -> Dict[str, Any]:
    """Mock LLM responses for triage service."""
    responses = {
        "default": {
            "triage": {
                "level": "self_care",
                "confidence": 0.85,
                "explanation": "Mild symptoms detected.",
            },
            "response": "This seems mild. Try rest and hydration.",
        }
    }

    class MockLLMClient:
        def __init__(self) -> None:
            self.calls: List[Dict[str, Any]] = []

        async def chat(self, messages: List[Dict[str, str]]) -> str:
            self.calls.append({"messages": messages})
            return responses["default"]["response"]

    client = MockLLMClient()
    return {"client": client, "responses": responses}


# ---------------------------------------------------------------------------
# httpx.AsyncClient with FastAPI app
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture(scope="function")
async def test_app(
    test_tables: DynamoDBManager,
    test_settings: Settings,
) -> AsyncGenerator[AsyncClient, None]:
    """Yield an httpx.AsyncClient wired to the FastAPI app."""
    # Override the DynamoDB manager dependency
    def _override_ddb():
        return test_tables

    app = create_app()
    app.dependency_overrides[get_dynamodb_manager] = _override_ddb

    # Reset metrics
    HealthService.reset_metrics()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()
