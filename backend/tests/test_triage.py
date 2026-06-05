"""Triage endpoint tests — LangGraph with MOCK_MODE."""

from httpx import AsyncClient


class TestTriageEndpoint:
    async def test_triage_returns_response(self, test_app: AsyncClient) -> None:
        resp = await test_app.post("/api/v1/triage", json={
            "query": "I have a mild headache",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "response" in data
        assert len(data["response"]) > 0

    async def test_triage_authenticated(self, test_app: AsyncClient, auth_headers: dict) -> None:
        resp = await test_app.post(
            "/api/v1/triage",
            json={"query": "I have a sore throat"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["response"]

    async def test_triage_requires_min_length(self, test_app: AsyncClient) -> None:
        resp = await test_app.post("/api/v1/triage", json={"query": "ab"})
        assert resp.status_code == 422
