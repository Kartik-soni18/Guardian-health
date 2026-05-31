"""Local prompt manager.

Prompts are loaded from local JSON files in app/prompt_hub/local/.
All prompts are cached in-memory after first load.
"""

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_CACHE: dict[str, str] = {}
_LOCAL_DIR = Path(__file__).parent / "local"

# Map friendly names to local filenames
_PROMPT_MAP: dict[str, str] = {
    "firewall": "firewall.json",
    "extraction": "extraction.json",
    "supervisor-scratchpad": "supervisor_scratchpad.json",
    "supervisor-reasoning": "supervisor_reasoning.json",
    "consultation": "consultation.json",
    "triage": "triage.json",
    "disease-info-with-diagnosis": "disease_info_with_diagnosis.json",
    "disease-info-no-diagnosis": "disease_info_no_diagnosis.json",
}


def _load_local(filename: str) -> str | None:
    path = _LOCAL_DIR / filename
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("prompt", data.get("template", data.get("content")))
    except Exception as exc:
        logger.warning("[Prompts] Failed to load local %s: %s", filename, exc)
        return None


def get_prompt(name: str, use_cache: bool = True) -> str:
    """Fetch a prompt by friendly name from local JSON storage."""
    if use_cache and name in _CACHE:
        return _CACHE[name]

    local_file = _PROMPT_MAP.get(name)
    if not local_file:
        raise ValueError(f"Unknown prompt name: {name}. Available: {list(_PROMPT_MAP.keys())}")

    local_prompt = _load_local(local_file)
    if local_prompt:
        _CACHE[name] = local_prompt
        return local_prompt

    raise RuntimeError(f"Prompt '{name}' unavailable. Local file missing: {local_file}")


def get_prompt_template(name: str, use_cache: bool = True) -> Any:
    """Return a LangChain ChatPromptTemplate if langchain is available.

    Falls back to a simple string template wrapper otherwise.
    """
    try:
        from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate
        text = get_prompt(name, use_cache=use_cache)
        return ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(text, template_format="f-string"),
        ])
    except ImportError:
        logger.debug("[Prompts] langchain_core not installed — returning raw string")
        return get_prompt(name, use_cache=use_cache)


def clear_cache() -> None:
    _CACHE.clear()


def list_prompts() -> list[str]:
    return list(_PROMPT_MAP.keys())
