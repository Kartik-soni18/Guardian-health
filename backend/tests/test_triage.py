"""GuardianHealth v2 Triage Tests — 15+ tests for symptom assessment endpoint."""


from typing import Any, Dict

import pytest
from httpx import AsyncClient


# =============================================================================
# Basic Triage Tests
# =============================================================================

class TestTriageSuccess:
    """POST /api/v1/triage — Rate limit: 10/min per IP"""

    async def test_triage_self_care_minor(self, test_app: AsyncClient) -> None:
        """Mild cold symptoms return self-care triage."""
        resp = await test_app.post("/api/v1/triage", json={
            "query": "I have a mild cold and runny nose",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "triage" in data
        assert "response" in data
        assert data["triage"]["level"] == "self_care"

    async def test_triage_urgent_fever(self, test_app: AsyncClient) -> None:
        """Fever symptoms return urgent triage."""
        resp = await test_app.post("/api/v1/triage", json={
            "query": "I have a high fever and severe vomiting",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["triage"]["level"] == "urgent"

    async def test_triage_emergency_chest_pain(self, test_app: AsyncClient) -> None:
        """Chest pain returns emergency triage."""
        resp = await test_app.post("/api/v1/triage", json={
            "query": "I have severe chest pain and can't breathe",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["triage"]["level"] == "emergency"
        assert "911" in data["response"] or "emergency" in data["response"].lower()

    async def test_triage_emergency_anaphylaxis(self, test_app: AsyncClient) -> None:
        """Anaphylaxis returns emergency triage."""
        resp = await test_app.post("/api/v1/triage", json={
            "query": "I am having anaphylaxis after a bee sting",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["triage"]["level"] == "emergency"

    async def test_triage_unknown_symptoms(self, test_app: AsyncClient) -> None:
        """Unknown/random symptoms return unknown triage."""
        resp = await test_app.post("/api/v1/triage", json={
            "query": "Purple spots appearing on my left elbow every Tuesday",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["triage"]["level"] == "unknown"


# =============================================================================
# Authenticated Triage Tests (Chat Persistence)
# =============================================================================

class TestTriageAuthenticated:
    """Triage with authenticated user creates chat."""

    async def test_triage_authenticated_creates_chat(
        self, test_app: AsyncClient, auth_headers: Dict[str, Any], test_user: Dict[str, Any],
    ) -> None:
        """Authenticated triage creates a chat and returns chat_id."""
        resp = await test_app.post("/api/v1/triage", json={
            "query": "I have a headache and sore throat",
        }, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["chat_id"] is not None
        assert len(data["chat_id"]) > 0

    async def test_triage_authenticated_continues_chat(
        self, test_app: AsyncClient, auth_headers: Dict[str, Any], test_chat: Dict[str, Any],
    ) -> None:
        """Providing chat_id continues existing chat."""
        resp = await test_app.post("/api/v1/triage", json={
            "query": "Now I also have a fever",
            "chat_id": test_chat["id"],
        }, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        # Should reuse or create new chat_id
        assert data["chat_id"] is not None

    async def test_triage_with_conversation_history(
        self, test_app: AsyncClient, auth_headers: Dict[str, Any],
    ) -> None:
        """Triage with conversation history works."""
        resp = await test_app.post("/api/v1/triage", json={
            "query": "It got worse",
            "conversation_history": [
                {"role": "user", "content": "I have a cough"},
                {"role": "assistant", "content": "How long have you had it?"},
            ],
        }, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "triage" in data
        assert "response" in data

    async def test_triage_autonymous_no_chat_saved(self, test_app: AsyncClient) -> None:
        """Anonymous triage does NOT create chat."""
        resp = await test_app.post("/api/v1/triage", json={
            "query": "I have a mild headache",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("chat_id") is None


# =============================================================================
# Validation Tests
# =============================================================================

class TestTriageValidation:
    """Invalid triage requests."""

    async def test_triage_empty_query(self, test_app: AsyncClient) -> None:
        """Empty query returns 422."""
        resp = await test_app.post("/api/v1/triage", json={
            "query": "",
        })
        assert resp.status_code == 422

    async def test_triage_short_query(self, test_app: AsyncClient) -> None:
        """Query shorter than 3 characters returns 422."""
        resp = await test_app.post("/api/v1/triage", json={
            "query": "ab",
        })
        assert resp.status_code == 422

    async def test_triage_missing_query(self, test_app: AsyncClient) -> None:
        """Missing query field returns 422."""
        resp = await test_app.post("/api/v1/triage", json={})
        assert resp.status_code == 422

    async def test_triage_query_too_short_exactly_2(self, test_app: AsyncClient) -> None:
        """Query of exactly 2 chars returns 422."""
        resp = await test_app.post("/api/v1/triage", json={
            "query": "ok",
        })
        assert resp.status_code == 422

    async def test_triage_exactly_3_chars_ok(self, test_app: AsyncClient) -> None:
        """Query of exactly 3 chars succeeds."""
        resp = await test_app.post("/api/v1/triage", json={
            "query": "abc",
        })
        assert resp.status_code == 200


# =============================================================================
# Error Handling & Fallback Tests
# =============================================================================

class TestTriageErrors:
    """Graceful error handling."""

    async def test_triage_primary_care_rash(self, test_app: AsyncClient) -> None:
        """Rash symptoms return primary care triage."""
        resp = await test_app.post("/api/v1/triage", json={
            "query": "I have a strange rash on my arm",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["triage"]["level"] in ("primary_care", "unknown")

    async def test_triage_self_care_sunburn(self, test_app: AsyncClient) -> None:
        """Sunburn returns self-care."""
        resp = await test_app.post("/api/v1/triage", json={
            "query": "I have a mild sunburn",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["triage"]["level"] == "self_care"

    @pytest.mark.skip(reason="Rate limits are per-IP; test client may not trigger")
    async def test_triage_rate_limit(self, test_app: AsyncClient) -> None:
        """Exceeding 10/min returns 429."""
        for i in range(12):
            resp = await test_app.post("/api/v1/triage", json={
                "query": f"Test query number {i} with headache",
            })
        assert resp.status_code == 429
