import logging
import json

from app import llm_client as gemini_client
from app.prompt_hub import get_prompt

_FIREWALL_SYSTEM_PROMPT = get_prompt("firewall")

logger = logging.getLogger(__name__)


def gate(user_query: str) -> dict | None:
    try:
        raw = gemini_client.call(
            system_prompt=_FIREWALL_SYSTEM_PROMPT,
            user_content=f"Classify this query: {user_query}",
            temperature=0.05,
            max_tokens=80,
            timeout=10.0,
        )
        raw = raw.strip("```json").strip("```").strip()
        parsed = json.loads(raw)
        is_medical = bool(parsed.get("is_medical", True))
        logger.info("[Firewall] is_medical=%s", is_medical)
        if not is_medical:
            return {"status": "rejected", "reason": "non-medical_query"}
        return None

    except (json.JSONDecodeError, KeyError, IndexError) as exc:
        logger.warning("[Firewall] Parse error: %s — fail-open", exc)
        return None

    except Exception as exc:
        logger.error("[Firewall] Error: %s — fail-open", exc)
        return None
