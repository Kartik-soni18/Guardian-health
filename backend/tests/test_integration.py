"""GuardianHealth v2 Integration Tests — 8+ end-to-end pipeline tests."""


from typing import Any, Dict

import pytest
from httpx import AsyncClient


# =============================================================================
# Full Pipeline Tests
# =============================================================================

class TestFullPipeline:
    """Complete user journeys."""

    async def test_pipeline_register_login_triage_list_get_delete(
        self, test_app: AsyncClient,
    ) -> None:
        """Full flow: register -> login -> triage -> list chats -> get chat -> delete."""
        # 1. Register
        register_resp = await test_app.post("/api/v1/auth/register", json={
            "username": "pipelineuser",
            "email": "pipeline@example.com",
            "password": "Pipeline123!",
            "full_name": "Pipeline User",
        })
        assert register_resp.status_code == 201
        tokens = register_resp.json()
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        # 2. Verify /me works
        me_resp = await test_app.get("/api/v1/auth/me", headers=headers)
        assert me_resp.status_code == 200
        assert me_resp.json()["username"] == "pipelineuser"

        # 3. Triage (authenticated)
        triage_resp = await test_app.post("/api/v1/triage", json={
            "query": "I have a headache and mild fever",
        }, headers=headers)
        assert triage_resp.status_code == 200
        triage_data = triage_resp.json()
        assert triage_data["chat_id"] is not None
        chat_id = triage_data["chat_id"]

        # 4. List chats
        list_resp = await test_app.get("/api/v1/chats", headers=headers)
        assert list_resp.status_code == 200
        list_data = list_resp.json()
        assert list_data["total"] >= 1
        assert any(c["id"] == chat_id for c in list_data["items"])

        # 5. Get specific chat
        get_resp = await test_app.get(f"/api/v1/chats/{chat_id}", headers=headers)
        assert get_resp.status_code == 200
        assert get_resp.json()["id"] == chat_id

        # 6. Delete chat
        del_resp = await test_app.delete(f"/api/v1/chats/{chat_id}", headers=headers)
        assert del_resp.status_code == 204

        # 7. Verify deletion
        get2_resp = await test_app.get(f"/api/v1/chats/{chat_id}", headers=headers)
        assert get2_resp.status_code == 404

    async def test_pipeline_login_with_registered_user(
        self, test_app: AsyncClient, test_user: Dict[str, Any],
    ) -> None:
        """Login with pre-seeded test user works."""
        resp = await test_app.post("/api/v1/auth/login", json={
            "username": test_user["username"],
            "password": "TestPass123!",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_pipeline_refresh_then_access_protected(
        self, test_app: AsyncClient, test_user: Dict[str, Any],
    ) -> None:
        """Login -> refresh -> access protected route."""
        # Login
        login_resp = await test_app.post("/api/v1/auth/login", json={
            "username": test_user["username"],
            "password": "TestPass123!",
        })
        refresh_token = login_resp.json()["refresh_token"]

        # Refresh
        refresh_resp = await test_app.post("/api/v1/auth/refresh", json={
            "refresh_token": refresh_token,
        })
        assert refresh_resp.status_code == 200
        new_access = refresh_resp.json()["access_token"]

        # Access protected route
        me_resp = await test_app.get("/api/v1/auth/me", headers={
            "Authorization": f"Bearer {new_access}",
        })
        assert me_resp.status_code == 200


# =============================================================================
# Anonymous Triage
# =============================================================================

class TestAnonymousTriage:
    """Triage without authentication."""

    async def test_anonymous_triage_no_chat_saved(self, test_app: AsyncClient) -> None:
        """Anonymous triage succeeds but no chat is persisted."""
        resp = await test_app.post("/api/v1/triage", json={
            "query": "I have a cough and sore throat",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["chat_id"] is None
        assert data["triage"]["level"] in ("self_care", "urgent", "unknown")

    async def test_anonymous_triage_emergency(self, test_app: AsyncClient) -> None:
        """Anonymous emergency triage works without auth."""
        resp = await test_app.post("/api/v1/triage", json={
            "query": "chest pain and can't breathe",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["triage"]["level"] == "emergency"


# =============================================================================
# Health Endpoints
# =============================================================================

class TestHealthEndpoints:
    """Health check endpoints."""

    async def test_health_status(self, test_app: AsyncClient) -> None:
        """GET /health returns status."""
        resp = await test_app.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data
        assert "version" in data
        assert "timestamp" in data
        assert "dynamodb" in data

    async def test_health_ready(self, test_app: AsyncClient) -> None:
        """GET /health/ready returns readiness."""
        resp = await test_app.get("/health/ready")
        assert resp.status_code == 200
        data = resp.json()
        assert "ready" in data
        assert "checks" in data

    async def test_health_live(self, test_app: AsyncClient) -> None:
        """GET /health/live returns liveness."""
        resp = await test_app.get("/health/live")
        assert resp.status_code == 200
        data = resp.json()
        assert data["alive"] is True

    async def test_health_metrics(self, test_app: AsyncClient) -> None:
        """GET /health/metrics returns metrics."""
        resp = await test_app.get("/health/metrics")
        assert resp.status_code == 200
        data = resp.json()
        assert "cache_stats" in data
        assert "request_counts" in data

    async def test_health_endpoints_no_auth_required(self, test_app: AsyncClient) -> None:
        """All health endpoints work without authentication."""
        for path in ["/health", "/health/ready", "/health/live", "/health/metrics"]:
            resp = await test_app.get(path)
            assert resp.status_code == 200, f"{path} failed"
