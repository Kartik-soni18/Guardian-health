"""Integration tests — auth + triage pipeline."""

from httpx import AsyncClient


class TestFullPipeline:
    async def test_register_login_triage(self, test_app: AsyncClient) -> None:
        register_resp = await test_app.post("/api/v1/auth/register", json={
            "username": "pipelineuser",
            "email": "pipeline@example.com",
            "password": "Pipeline123!",
            "full_name": "Pipeline User",
        })
        assert register_resp.status_code == 201
        tokens = register_resp.json()
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        me_resp = await test_app.get("/api/v1/auth/me", headers=headers)
        assert me_resp.status_code == 200
        assert me_resp.json()["username"] == "pipelineuser"

        triage_resp = await test_app.post(
            "/api/v1/triage",
            json={"query": "I have a headache and mild fever"},
            headers=headers,
        )
        assert triage_resp.status_code == 200
        assert triage_resp.json()["response"]

    async def test_health_check(self, test_app: AsyncClient) -> None:
        resp = await test_app.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] in ("healthy", "degraded")
        assert "mongodb" in data
