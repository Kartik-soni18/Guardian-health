"""GuardianHealth v2 Chat Tests — 12+ tests for CRUD operations."""


from typing import Any, Dict

import pytest
from httpx import AsyncClient


# =============================================================================
# List Chats
# =============================================================================

class TestListChats:
    """GET /api/v1/chats — List user's chats"""

    async def test_list_authenticated_with_chats(
        self, test_app: AsyncClient, auth_headers: Dict[str, Any], test_chat: Dict[str, Any],
    ) -> None:
        """Authenticated user sees their chats."""
        resp = await test_app.get("/api/v1/chats", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        assert len(data["items"]) >= 1
        assert any(item["id"] == test_chat["id"] for item in data["items"])

    async def test_list_authenticated_empty(
        self, test_app: AsyncClient, auth_headers: Dict[str, Any],
    ) -> None:
        """User with no chats gets empty list."""
        resp = await test_app.get("/api/v1/chats", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["items"] == []

    async def test_list_unauthenticated(self, test_app: AsyncClient) -> None:
        """Unauthenticated request returns 401."""
        resp = await test_app.get("/api/v1/chats")
        assert resp.status_code == 401


# =============================================================================
# Get Chat
# =============================================================================

class TestGetChat:
    """GET /api/v1/chats/{chat_id} — Get chat details"""

    async def test_get_success(
        self, test_app: AsyncClient, auth_headers: Dict[str, Any], test_chat: Dict[str, Any],
    ) -> None:
        """Owner can retrieve their chat."""
        resp = await test_app.get(f"/api/v1/chats/{test_chat['id']}", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == test_chat["id"]
        assert data["title"] == test_chat["title"]

    async def test_get_not_owner(
        self, test_app: AsyncClient, other_auth_headers: Dict[str, Any], test_chat: Dict[str, Any],
    ) -> None:
        """Non-owner gets 403."""
        resp = await test_app.get(f"/api/v1/chats/{test_chat['id']}", headers=other_auth_headers)
        assert resp.status_code == 403
        assert "owner" in resp.json()["detail"].lower() or "not" in resp.json()["detail"].lower()

    async def test_get_not_found(
        self, test_app: AsyncClient, auth_headers: Dict[str, Any],
    ) -> None:
        """Nonexistent chat returns 404."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        resp = await test_app.get(f"/api/v1/chats/{fake_id}", headers=auth_headers)
        assert resp.status_code == 404

    async def test_get_unauthenticated(self, test_app: AsyncClient, test_chat: Dict[str, Any]) -> None:
        """Unauthenticated request returns 401."""
        resp = await test_app.get(f"/api/v1/chats/{test_chat['id']}")
        assert resp.status_code == 401

    async def test_get_invalid_chat_id_format(self, test_app: AsyncClient, auth_headers: Dict[str, Any]) -> None:
        """Invalid chat ID format returns 404 (not found after lookup)."""
        resp = await test_app.get("/api/v1/chats/not-a-valid-uuid", headers=auth_headers)
        assert resp.status_code == 404


# =============================================================================
# Delete Chat
# =============================================================================

class TestDeleteChat:
    """DELETE /api/v1/chats/{chat_id} — Delete chat"""

    async def test_delete_success(
        self, test_app: AsyncClient, auth_headers: Dict[str, Any], test_chat: Dict[str, Any],
    ) -> None:
        """Owner can delete their chat."""
        resp = await test_app.delete(f"/api/v1/chats/{test_chat['id']}", headers=auth_headers)
        assert resp.status_code == 204

        # Verify it's gone
        get_resp = await test_app.get(f"/api/v1/chats/{test_chat['id']}", headers=auth_headers)
        assert get_resp.status_code == 404

    async def test_delete_not_owner(
        self, test_app: AsyncClient, other_auth_headers: Dict[str, Any], test_chat: Dict[str, Any],
    ) -> None:
        """Non-owner cannot delete — gets 403."""
        resp = await test_app.delete(f"/api/v1/chats/{test_chat['id']}", headers=other_auth_headers)
        assert resp.status_code == 403

    async def test_delete_not_found(
        self, test_app: AsyncClient, auth_headers: Dict[str, Any],
    ) -> None:
        """Deleting nonexistent chat returns 404."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        resp = await test_app.delete(f"/api/v1/chats/{fake_id}", headers=auth_headers)
        assert resp.status_code == 404

    async def test_delete_unauthenticated(self, test_app: AsyncClient, test_chat: Dict[str, Any]) -> None:
        """Unauthenticated delete returns 401."""
        resp = await test_app.delete(f"/api/v1/chats/{test_chat['id']}")
        assert resp.status_code == 401
