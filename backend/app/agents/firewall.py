"""
Firewall Agent — Validates whether a query is medical/health-related.

- Fast path: emergency keyword detection
- LLM-based classification with structured JSON output
- Fail-open on errors (for safety-critical health queries)
"""


import asyncio
import logging
import re
from pathlib import Path

from app.agents.llm_client import AsyncLLMClient

logger = logging.getLogger("guardian.firewall")

# ---------------------------------------------------------------------------
# Emergency keywords for fast-path triage
# ---------------------------------------------------------------------------
EMERGENCY_KEYWORDS = [
    "chest pain",
    "heart attack",
    "can't breathe",
    "cannot breathe",
    "difficulty breathing",
    "shortness of breath",
    "unconscious",
    "passed out",
    "fainted",
    "seizure",
    "stroke",
    "severe bleeding",
    "bleeding heavily",
    "suicide",
    "suicidal",
    "overdose",
    "poisoning",
    "anaphylaxis",
    "allergic reaction",
    "swelling throat",
    "can't swallow",
    "head injury",
    "broken bone",
    "burn",
    "electrocution",
    "drowning",
    "baby not breathing",
    "pregnant and bleeding",
    "severe abdominal pain",
    "vision loss",
    "paralyzed",
    "slurred speech",
]

FIREWALL_PROMPT_PATH = Path(__file__).with_suffix("").parent / "prompts" / "firewall.txt"


def _check_emergency_keywords(text: str) -> bool:
    """Fast-path check for emergency keywords."""
    lowered = text.lower()
    return any(kw in lowered for kw in EMERGENCY_KEYWORDS)


async def firewall_gate(query: str, llm: AsyncLLMClient) -> dict:
    """
    Determine if the query is medical and appropriate for triage.

    Returns dict with keys:
        is_medical: bool
        is_emergency: bool
        reason: str
        rejection_category: str | None
    """
    # ---- Fast path: emergency keywords always pass through ----
    if _check_emergency_keywords(query):
        logger.info("Firewall fast-path: emergency keyword detected")
        return {
            "is_medical": True,
            "is_emergency": True,
            "reason": "Emergency keywords detected — fast-track to triage",
            "rejection_category": None,
        }

    # ---- LLM classification ----
    try:
        prompt_text = FIREWALL_PROMPT_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        logger.error("Firewall prompt file not found at %s", FIREWALL_PROMPT_PATH)
        # Fail-open: accept the query if we can't validate
        return {
            "is_medical": True,
            "is_emergency": False,
            "reason": "Prompt file missing — fail-open for safety",
            "rejection_category": None,
        }

    try:
        result = await llm.parse_json(
            system_prompt=prompt_text,
            user_content=f'User query: """{query}"""\n\nClassify this query.',
            node_type="firewall",
            max_tokens=256,
        )

        is_medical = bool(result.get("is_medical", True))
        is_emergency = bool(result.get("is_emergency", False))
        reason = result.get("reason", "No reason provided")
        rejection_category = result.get("rejection_category")

        logger.info(
            "Firewall decision: medical=%s emergency=%s reason=%s",
            is_medical,
            is_emergency,
            reason,
        )

        return {
            "is_medical": is_medical,
            "is_emergency": is_emergency,
            "reason": reason,
            "rejection_category": rejection_category,
        }

    except Exception as exc:
        logger.error("Firewall LLM call failed: %s — failing open", exc)
        # Fail-open: accept query on error (safety-critical)
        return {
            "is_medical": True,
            "is_emergency": False,
            "reason": f"Firewall error ({type(exc).__name__}) — fail-open",
            "rejection_category": None,
        }
