"""Abstract base agent with standardized execution, retry, and metrics."""

import json
import logging
import time
from abc import ABC, abstractmethod
from typing import Any

from app.harness.types import AgentState

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Every GuardianHealth agent inherits from BaseAgent.

    Provides:
      - Structured JSON output parsing (strips markdown fences).
      - Retry with exponential backoff.
      - Automatic metrics emission (latency, tokens if available).
      - Graceful degradation on failure.
    """

    name: str = "base_agent"
    max_retries: int = 2
    backoff_seconds: float = 1.0

    @abstractmethod
    async def invoke(self, state: AgentState) -> dict[str, Any]:
        """Execute the agent's core logic.

        Must return a dict of state updates (partial AgentState).
        """
        ...

    async def run(self, state: AgentState) -> AgentState:
        """Run the agent with retry logic, metrics, and error handling.

        Returns a *new* state dict with updates merged in.
        """
        merged = dict(state)
        last_error = None

        for attempt in range(1, self.max_retries + 1):
            start = time.time()
            try:
                updates = await self.invoke(merged)
                latency_ms = int((time.time() - start) * 1000)
                updates["_last_agent"] = self.name
                updates["_last_latency_ms"] = latency_ms
                merged.update(updates)
                return merged  # type: ignore[return-value]
            except Exception as exc:
                last_error = exc
                latency_ms = int((time.time() - start) * 1000)
                logger.warning(
                    "[%s] Attempt %d/%d failed: %s",
                    self.name,
                    attempt,
                    self.max_retries,
                    exc,
                )
                if attempt < self.max_retries:
                    time.sleep(self.backoff_seconds * (2 ** (attempt - 1)))

        # All retries exhausted — merge a graceful failure marker
        logger.error("[%s] All retries exhausted: %s", self.name, last_error)
        merged.update(self._fallback(state, last_error))
        return merged  # type: ignore[return-value]

    def _fallback(self, state: AgentState, error: Exception | None) -> dict[str, Any]:
        """Return a safe fallback state update when all retries fail.

        Subclasses may override to provide domain-specific fallbacks.
        """
        return {
            "_error": f"{self.name} failed after {self.max_retries} attempts: {error}",
        }

    @staticmethod
    def parse_json(raw: str) -> dict[str, Any]:
        """Strip markdown fences and parse JSON."""
        cleaned = (
            raw.strip()
            .removeprefix("```json")
            .removeprefix("```")
            .removesuffix("```")
            .strip()
        )
        return json.loads(cleaned)
