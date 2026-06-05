"""Async LLM client for Together.ai with mock mode for tests."""

import asyncio
import json
import logging
import time
from typing import Any

import httpx
import json_repair
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.config import get_settings

logger = logging.getLogger("guardian.llm")

TEMPERATURE_PROFILES: dict[str, float] = {
    "firewall": 0.1,
    "extraction": 0.2,
    "scratchpad": 0.2,
    "reasoning": 0.3,
    "consultation": 0.4,
    "triage": 0.3,
    "disease_info": 0.3,
}

MOCK_RESPONSES: dict[str, str] = {
    "firewall": json.dumps({"is_medical": True, "reason": "Mock: medical keywords detected"}),
    "extraction": json.dumps({
        "symptoms": ["headache"],
        "duration": "2 days",
        "severity": "mild",
        "search_terms": ["headache"],
    }),
    "reasoning": json.dumps({
        "observations": "Patient reports mild headache.",
        "differentials": ["tension headache", "migraine"],
        "red_flags": [],
        "missing_info": ["Duration?"],
        "confidence": 0.7,
    }),
    "consultation": json.dumps({
        "assessment": "Likely benign headache.",
        "plan": "Rest, hydration, OTC analgesics.",
        "disclaimer": "Not a diagnosis.",
        "references": [],
    }),
    "triage": json.dumps({
        "level": "routine",
        "care_setting": "self_care",
        "explanation": "Mild symptoms manageable at home.",
        "action": "Rest and monitor.",
        "wait_time": "N/A",
    }),
    "disease_info": json.dumps({
        "condition": "Tension Headache",
        "description": "Common headache often related to stress.",
        "symptoms": ["dull head pain"],
        "when_to_seek": "Seek care if sudden severe headache.",
        "common_tests": [],
        "follow_up": "Primary care if persistent.",
    }),
}


def _prompts_dir() -> "Path":
    from pathlib import Path
    return Path(__file__).resolve().parent / "prompts"


class AsyncLLMClient:
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        mock_mode: bool | None = None,
        timeout: float = 60.0,
    ) -> None:
        settings = get_settings()
        self.api_key = api_key or settings.together_api_key or ""
        self.base_url = (base_url or settings.together_base_url).rstrip("/")
        self.model = model or settings.together_model
        self.mock_mode = mock_mode if mock_mode is not None else settings.mock_mode
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
        @retry(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=2, max=10),
            retry=retry_if_exception_type((httpx.TimeoutException, httpx.HTTPStatusError)),
            reraise=True,
        )
        async def _post() -> dict[str, Any]:
            resp = await self.client.post(f"{self.base_url}/chat/completions", json=payload)
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
        if self.mock_mode:
            logger.info("[MOCK] node_type=%s", node_type)
            await asyncio.sleep(0.02)
            return MOCK_RESPONSES.get(
                node_type,
                json.dumps({"mock": True, "node_type": node_type}),
            )

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            "temperature": TEMPERATURE_PROFILES.get(node_type, 0.3),
            "max_tokens": max_tokens,
        }

        start = time.perf_counter()
        try:
            data = await self._post_with_retry(payload)
            content = data["choices"][0]["message"]["content"]
            logger.info(
                "LLM ok node=%s latency=%.1fms",
                node_type,
                (time.perf_counter() - start) * 1000,
            )
            return content
        except Exception as exc:
            logger.error("LLM FAILED node=%s error=%s", node_type, exc)
            raise

    async def parse_json(
        self,
        system_prompt: str,
        user_content: str,
        node_type: str,
        max_tokens: int = 1024,
    ) -> dict[str, Any]:
        raw = await self.call(system_prompt, user_content, node_type, max_tokens)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            repaired = json_repair.repair_json(raw)
            if isinstance(repaired, str):
                return json.loads(repaired)
            return repaired
