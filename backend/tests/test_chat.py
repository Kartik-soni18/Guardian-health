"""Chat persistence tests — CRUD, ownership, triage integration."""

from typing import Any, Dict

import pytest
from httpx import AsyncClient

from app.core.security import create_token_pair, get_password_hash
from app.db.mongodb import MongoDBManager


@pytest.fixture
async def other_user(test_db: MongoDBManager) -> Dict[str, Any]:
    return await test_db.create_user({
        "username": "otheruser",
        "password_hash": get_password_hash("OtherPass123!"),
    })


@pytest.fixture
def other_auth_headers(other_user: Dict[str, Any]) -> Dict[str, str]:
    access_token, _ = create_token_pair(
        other_user["username"],
        extra_claims={"uid": other_user["id"]},
    )
    return {"Authorization": f"Bearer {access_token}"}


class TestChatCRUD:
    async def test_create_and_list_chats(
        self,
        test_app: AsyncClient,
        auth_headers: dict,
    ) -> None:
        create_resp = await test_app.post(
            "/api/v1/chats",
            json={"initialMessage": "I have a fever"},
            headers=auth_headers,
        )
        assert create_resp.status_code == 201
        chat = create_resp.json()
        assert chat["id"]
        assert chat["title"] == "I have a fever"
        assert chat["userId"]

        list_resp = await test_app.get("/api/v1/chats", headers=auth_headers)
        assert list_resp.status_code == 200
        chats = list_resp.json()
        assert len(chats) == 1
        assert chats[0]["id"] == chat["id"]

    async def test_get_chat_with_messages(
        self,
        test_app: AsyncClient,
        auth_headers: dict,
    ) -> None:
        create_resp = await test_app.post(
            "/api/v1/chats",
            json={},
            headers=auth_headers,
        )
        chat_id = create_resp.json()["id"]

        triage_resp = await test_app.post(
            "/api/v1/triage",
            json={"query": "I have a mild headache", "chat_id": chat_id},
            headers=auth_headers,
        )
        assert triage_resp.status_code == 200

        detail_resp = await test_app.get(
            f"/api/v1/chats/{chat_id}",
            headers=auth_headers,
        )
        assert detail_resp.status_code == 200
        detail = detail_resp.json()
        assert len(detail["messages"]) == 2
        assert detail["messages"][0]["role"] == "user"
        assert detail["messages"][1]["role"] == "assistant"

    async def test_delete_chat(
        self,
        test_app: AsyncClient,
        auth_headers: dict,
    ) -> None:
        create_resp = await test_app.post("/api/v1/chats", json={}, headers=auth_headers)
        chat_id = create_resp.json()["id"]

        delete_resp = await test_app.delete(
            f"/api/v1/chats/{chat_id}",
            headers=auth_headers,
        )
        assert delete_resp.status_code == 204

        get_resp = await test_app.get(
            f"/api/v1/chats/{chat_id}",
            headers=auth_headers,
        )
        assert get_resp.status_code == 404

    async def test_requires_auth(self, test_app: AsyncClient) -> None:
        resp = await test_app.get("/api/v1/chats")
        assert resp.status_code == 401


class TestChatOwnership:
    async def test_cannot_access_other_users_chat(
        self,
        test_app: AsyncClient,
        auth_headers: dict,
        other_auth_headers: dict,
    ) -> None:
        create_resp = await test_app.post("/api/v1/chats", json={}, headers=auth_headers)
        chat_id = create_resp.json()["id"]

        get_resp = await test_app.get(
            f"/api/v1/chats/{chat_id}",
            headers=other_auth_headers,
        )
        assert get_resp.status_code == 404

        delete_resp = await test_app.delete(
            f"/api/v1/chats/{chat_id}",
            headers=other_auth_headers,
        )
        assert delete_resp.status_code == 404


class TestTriageChatPersistence:
    async def test_triage_loads_server_history(
        self,
        test_app: AsyncClient,
        auth_headers: dict,
    ) -> None:
        create_resp = await test_app.post("/api/v1/chats", json={}, headers=auth_headers)
        chat_id = create_resp.json()["id"]

        first = await test_app.post(
            "/api/v1/triage",
            json={"query": "I have ankle pain after running", "chat_id": chat_id},
            headers=auth_headers,
        )
        assert first.status_code == 200

        second = await test_app.post(
            "/api/v1/triage",
            json={
                "query": "It started one day ago",
                "chat_id": chat_id,
                "conversation_history": [
                    {"role": "user", "content": "ignored stale client history"},
                ],
            },
            headers=auth_headers,
        )
        assert second.status_code == 200

        detail_resp = await test_app.get(
            f"/api/v1/chats/{chat_id}",
            headers=auth_headers,
        )
        messages = detail_resp.json()["messages"]
        assert len(messages) == 4
        assert messages[0]["content"] == "I have ankle pain after running"
        assert messages[2]["content"] == "It started one day ago"

    async def test_user_message_scrubbed_on_persist(
        self,
        test_app: AsyncClient,
        auth_headers: dict,
    ) -> None:
        create_resp = await test_app.post("/api/v1/chats", json={}, headers=auth_headers)
        chat_id = create_resp.json()["id"]

        await test_app.post(
            "/api/v1/triage",
            json={
                "query": "My email is patient@example.com and I have fever",
                "chat_id": chat_id,
            },
            headers=auth_headers,
        )

        detail_resp = await test_app.get(
            f"/api/v1/chats/{chat_id}",
            headers=auth_headers,
        )
        user_message = detail_resp.json()["messages"][0]["content"]
        assert "patient@example.com" not in user_message
        assert "[EMAIL_REDACTED]" in user_message

    async def test_triage_unknown_chat_returns_404(
        self,
        test_app: AsyncClient,
        auth_headers: dict,
    ) -> None:
        resp = await test_app.post(
            "/api/v1/triage",
            json={"query": "I have a headache", "chat_id": "00000000-0000-0000-0000-000000000000"},
            headers=auth_headers,
        )
        assert resp.status_code == 404
