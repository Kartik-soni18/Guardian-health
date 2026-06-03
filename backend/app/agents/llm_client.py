"""
AsyncLLMClient — Fully async LLM client with retries, mock mode, and latency logging.

Uses httpx.AsyncClient for all outbound calls. Tenacity for retries.
json_repair for robust JSON parsing. Temperature profiles per node_type.
"""


import json
import logging
import os
import time
from pathlib import Path
from typing import Any

import httpx
import json_repair
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger("guardian.llm")

# ---------------------------------------------------------------------------
# Temperature profiles per node type
# ---------------------------------------------------------------------------
TEMPERATURE_PROFILES: dict[str, float] = {
    "firewall": 0.1,
    "extraction": 0.2,
    "scratchpad": 0.2,
    "reasoning": 0.3,
    "consultation": 0.4,
    "triage": 0.3,
    "disease_info": 0.3,
}

# ---------------------------------------------------------------------------
# Mock responses for dev / CI (no API key needed)
# ---------------------------------------------------------------------------
MOCK_RESPONSES: dict[str, str] = {
    "firewall": json.dumps({"is_medical": True, "reason": "Mock: medical keywords detected"}),
    "extraction": json.dumps({
        "symptoms": ["chest pain", "shortness of breath"],
        "duration": "2 days",
        "severity": "moderate",
        "search_terms": ["chest pain", "dyspnea"],
    }),
    "scratchpad": json.dumps({
        "observations": "Patient reports chest pain and dyspnea.",
        "considerations": "Consider cardiac workup; rule out MI, PE.",
        "confidence": 0.72,
    }),
    "reasoning": json.dumps({
        "ml_reasoning": "Top predictions: ACS (0.65), PE (0.20), GERD (0.10).",
        "discrepancy_note": "",
        "confidence": 0.65,
    }),
    "consultation": json.dumps({
        "assessment": "Possible acute coronary syndrome given chest pain + dyspnea.",
        "plan": "Recommend immediate ED evaluation. ECG and troponins advised.",
        "disclaimer": "This is not a diagnosis. Seek emergency care.",
        "references": ["ACC/AHA Chest Pain Guidelines 2022"],
    }),
    "triage": json.dumps({
        "level": "emergent",
        "explanation": "Chest pain with dyspnea may indicate life-threatening condition.",
        "action": "Go to nearest emergency department immediately.",
        "wait_time": "Immediate",
    }),
    "disease_info": json.dumps({
        "condition": "Acute Coronary Syndrome",
        "description": "A spectrum of conditions caused by sudden reduced blood flow to the heart.",
        "symptoms": ["chest pain", "shortness of breath", "nausea", "sweating"],
        "when_to_seek": "Emergency care immediately if chest pain is severe or accompanied by dyspnea.",
        "common_tests": ["ECG", "Troponin", "Chest X-ray"],
        "follow_up": "Cardiology follow-up after acute management.",
    }),
}


class AsyncLLMClient:
    """Async LLM client with retry logic, mock mode, and per-node temperature profiles."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = "https://api.openai.com/v1",
        model: str = "gpt-4o-mini",
        mock_mode: bool | None = None,
        timeout: float = 60.0,
    ) -> None:
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.mock_mode = (
            mock_mode
            if mock_mode is not None
            else os.getenv("LLM_MOCK_MODE", "false").lower() == "true"
        )
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout, connect=10.0),
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def _post_with_retry(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Execute HTTP POST with tenacity retries."""

        @retry(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=2, max=10),
            retry=retry_if_exception_type(
                (httpx.TimeoutException, httpx.HTTPStatusError)
            ),
            reraise=True,
        )
        async def _post() -> dict[str, Any]:
            resp = await self.client.post(
                f"{self.base_url}/chat/completions", json=payload
            )
            resp.raise_for_status()
            return resp.json()

        return await _post()

    async def call(
        self,
        system_prompt: str,
        user_content: str,
        node_type: str,
        max_tokens: int = 1024,
    ) -> str:
        """
        Call the LLM with the given prompt and return the raw text content.

        Args:
            system_prompt: System-level instruction.
            user_content: User message content.
            node_type: One of firewall|extraction|scratchpad|reasoning|consultation|triage|disease_info.
            max_tokens: Max tokens to generate.

        Returns:
            Raw string response from the LLM (or mock).
        """
        if self.mock_mode:
            logger.info("[MOCK] node_type=%s — returning canned response", node_type)
            await asyncio.sleep(0.05)  # tiny realism
            return MOCK_RESPONSES.get(
                node_type,
                json.dumps({"mock": True, "node_type": node_type}),
            )

        temperature = TEMPERATURE_PROFILES.get(node_type, 0.3)

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        start = time.perf_counter()
        try:
            data = await self._post_with_retry(payload)
            latency_ms = (time.perf_counter() - start) * 1000
            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            logger.info(
                "LLM call ok node=%s latency=%.1fms tokens=%s",
                node_type,
                latency_ms,
                usage,
            )
            return content
        except Exception as exc:
            latency_ms = (time.perf_counter() - start) * 1000
            logger.error(
                "LLM call FAILED node=%s latency=%.1fms error=%s",
                node_type,
                latency_ms,
                exc,
            )
            raise

    async def parse_json(
        self,
        system_prompt: str,
        user_content: str,
        node_type: str,
        max_tokens: int = 1024,
    ) -> dict[str, Any]:
        """
        Call the LLM and parse the response as JSON (with json_repair fallback).
        """
        raw = await self.call(system_prompt, user_content, node_type, max_tokens)
        try:
            return json.loads(raw)  # type: ignore[arg-type]
        except json.JSONDecodeError:
            logger.warning("JSON parse failed for node=%s, attempting repair", node_type)
            repaired = json_repair.repair_json(raw)
            if isinstance(repaired, str):
                return json.loads(repaired)
            return repaired  # type: ignore[return-value]


# Lazy import to avoid issues at module load
import asyncio  # noqa: E402
