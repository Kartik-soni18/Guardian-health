import json
import logging
import os
import random
import time
from typing import Any
import httpx

logger = logging.getLogger(__name__)

_API_KEY   = os.getenv("TOGETHER_API_KEY")
_MODEL     = os.getenv("TOGETHER_MODEL", "meta-llama/Llama-3.3-70B-Instruct-Turbo")
_BASE      = "https://api.together.xyz/v1/chat/completions"
_ENV       = os.getenv("GUARDIAN_ENV", "production").lower()
_MOCK_MODE = os.getenv("MOCK_MODE", "false").lower() in ("true", "1", "yes")

# ── MOCK_MODE security gate ───────────────────────────────────────────────────
# Mock mode is ONLY permitted in development/test environments.
# In production, missing API key is a hard error — never fall back to canned responses.
_MOCK_ALLOWED = _ENV in ("development", "dev", "test", "testing")
if _MOCK_MODE and not _MOCK_ALLOWED:
    logger.critical(
        "MOCK_MODE is enabled but GUARDIAN_ENV=%s. "
        "Mock responses are forbidden in production. Set GUARDIAN_ENV=development for testing.",
        _ENV,
    )
    _MOCK_MODE = False

# ── Temperature profiles per node type ────────────────────────────────────────
# Extraction / reasoning → low temp for consistency
# Triage / consultation → higher temp for linguistic variety and warmth
TEMPERATURE_PROFILES = {
    "default": 0.3,
    "extraction": 0.2,
    "firewall": 0.1,
    "scratchpad": 0.2,
    "reasoning": 0.3,
    "consultation": 0.5,
    "triage": 0.6,
    "disease_info": 0.4,
    "g_eval": 0.1,
}


def _get_temperature(system_prompt: str, override: float | None = None) -> float:
    """Return the appropriate temperature based on prompt content or explicit override."""
    if override is not None:
        return override
    sp = system_prompt.lower()
    if '"is_medical"' in system_prompt:
        return TEMPERATURE_PROFILES["firewall"]
    if '"search_terms"' in system_prompt and '"symptoms"' in system_prompt:
        return TEMPERATURE_PROFILES["extraction"]
    if '"scratchpad"' in system_prompt:
        return TEMPERATURE_PROFILES["scratchpad"]
    if '"ml_assessment"' in system_prompt:
        return TEMPERATURE_PROFILES["reasoning"]
    if '"ready_for_triage"' in system_prompt:
        return TEMPERATURE_PROFILES["consultation"]
    if '"level"' in system_prompt and "self-care" in sp:
        return TEMPERATURE_PROFILES["triage"]
    if '"cures"' in system_prompt:
        return TEMPERATURE_PROFILES["disease_info"]
    if '"hallucination"' in system_prompt:
        return TEMPERATURE_PROFILES["g_eval"]
    return TEMPERATURE_PROFILES["default"]


# ── Dynamic mock response generator ───────────────────────────────────────────
# Instead of identical canned JSON, we generate context-aware mock responses
# that vary per call to avoid the "repeated answer every time" problem.

def _mock_response(system_prompt: str, user_content: str) -> str:
    uc = user_content.lower()

    # Medical Firewall — expects {"is_medical": ...}
    if '"is_medical"' in system_prompt:
        non_medical = any(k in uc for k in ["capital", "poem", "weather", "math", "2+2", "france", "ocean"])
        return json.dumps({
            "is_medical": not non_medical,
            "reason": "Health query" if not non_medical else "Non-medical query detected",
        })

    # Clinical entity extractor — expects {"symptoms", "search_terms", ...}
    if '"search_terms"' in system_prompt and '"symptoms"' in system_prompt:
        symptoms = []
        if "headache" in uc:           symptoms.append("headache")
        if "chest" in uc:              symptoms.append("chest_pain")
        if "breath" in uc:             symptoms.append("breathlessness")
        if "fever" in uc or "chill" in uc: symptoms.append("high_fever")
        if "cut" in uc or "bleed" in uc or "wound" in uc:
            symptoms.append("skin_wound")
        if "dizzy" in uc or "nausea" in uc: symptoms.append("dizziness")
        if "stomach" in uc or "abdominal" in uc: symptoms.append("stomach_pain")
        if "cough" in uc:              symptoms.append("cough")
        if "sore throat" in uc:        symptoms.append("sore_throat")
        if "fatigue" in uc or "tired" in uc: symptoms.append("fatigue")
        if not symptoms:
            symptoms = ["general_discomfort"]
        return json.dumps({
            "symptoms": symptoms,
            "duration": _infer_duration(uc),
            "severity": _infer_severity(uc),
            "search_terms": symptoms[:2] or ["general symptoms"],
        })

    # Supervisor scratchpad — expects {"scratchpad", "routing_decision", ...}
    if '"scratchpad"' in system_prompt:
        return json.dumps({
            "scratchpad": _vary_text([
                "Patient presents with symptoms requiring structured assessment. Privacy and diagnostic checks will run first.",
                "Reviewing patient input: symptoms noted, PII scrub planned, ML diagnostic next.",
                "Initial assessment: gather clinical entities, run Guardian-ML model, then route based on confidence.",
            ]),
            "worker_order": ["privacy_officer", "diagnostic_specialist", "compliance_auditor"],
            "routing_decision": "consultation",
            "key_risks": None,
        })

    # Supervisor reasoning over ML — expects {"ml_assessment", "discrepancy_detected", ...}
    if '"ml_assessment"' in system_prompt:
        emergency = any(k in uc for k in [
            "can't breathe", "cannot breathe", "difficulty breathing", "breathless",
            "heart attack", "unconscious", "seizure", "911",
        ])
        return json.dumps({
            "ml_assessment": _vary_text([
                "The ML prediction aligns with the reported symptom profile.",
                "Guardian-ML output appears plausible given patient description.",
                "Clinical correlation with ML suggestion is reasonable; no major discrepancy.",
            ]),
            "discrepancy_detected": False,
            "discrepancy_note": None,
            "emergency_detected": emergency,
            "final_routing": "emergency" if emergency else "consultation",
        })

    # Consultation agent — expects {"ready_for_triage", ...}
    if '"ready_for_triage"' in system_prompt:
        return json.dumps({
            "ready_for_triage": True,
            "follow_up_message": "",
            "gathered_context": uc[:120],
            "current_state": "ready",
        })

    # Triage agent — expects {"level": "Self-Care | Urgent Care | Emergency Room", ...}
    if '"level"' in system_prompt and "self-care" in system_prompt.lower():
        if any(k in uc for k in ["chest_pain", "chest pain", "breathless", "difficulty breath", "heart attack", "unconscious"]):
            level = "Emergency Room"
            reasoning = _vary_text([
                "Your symptoms suggest a potentially serious condition that requires immediate evaluation in an emergency setting. Please consult a licensed healthcare professional.",
                "Given the nature of what you're describing, it's important to seek emergency care right away. Please consult a licensed healthcare professional.",
            ])
            red_flags = ["Chest pain or pressure", "Difficulty breathing", "Loss of consciousness"]
        elif any(k in uc for k in ["small cut", "minor cut", "cut on my finger", "little cut", "scratch", "mild headache"]):
            level = "Self-Care"
            reasoning = _vary_text([
                "Your symptoms appear mild and can likely be managed at home with basic self-care. Please consult a licensed healthcare professional if they worsen.",
                "This sounds like a minor issue that typically responds well to home remedies. Please consult a licensed healthcare professional if anything changes.",
            ])
            red_flags = ["Worsening pain", "Signs of infection", "New symptoms develop"]
        else:
            level = "Urgent Care"
            reasoning = _vary_text([
                "Your symptoms warrant a professional evaluation. Visiting an urgent care clinic would be appropriate. Please consult a licensed healthcare professional.",
                "Based on what you've shared, it's best to have a clinician assess you soon. Please consult a licensed healthcare professional.",
            ])
            red_flags = ["Fever not responding to medication", "Symptoms getting worse", "Difficulty breathing"]
        return json.dumps({
            "level": level,
            "reasoning": reasoning,
            "red_flags": red_flags,
            "guideline_source": "GuardianHealth Clinical Protocol",
            "remedies": random.sample(["Rest", "Stay hydrated", "Apply ice pack", "Elevate affected area", "Warm compress"], k=2),
        })

    # Disease info — expects {"cures", "otc_products", ...}
    if '"cures"' in system_prompt:
        return json.dumps({
            "cures": _vary_text(["Rest and adequate hydration", "Over-the-counter symptom relief as appropriate"], list_mode=True),
            "prevention": ["Good hygiene practices", "Adequate sleep", "Balanced nutrition"],
            "self_care": random.sample(["Rest", "Drink fluids", "Light activity only", "Monitor temperature", "Stay in a comfortable environment"], k=2),
            "emergency_signs": ["Worsening symptoms", "Difficulty breathing", "Chest pain", "Confusion"],
            "otc_products": random.sample(["Paracetamol", "Ibuprofen", "ORS Sachets", "Antacid Tablets", "Cetirizine", "Vitamin C 500mg"], k=3),
        })

    # G-Eval scorer — expects {"relevance", "safety", ...}
    if '"hallucination"' in system_prompt:
        return json.dumps({
            "relevance": random.randint(3, 5),
            "safety": random.randint(4, 5),
            "coherence": random.randint(3, 5),
            "groundedness": random.randint(3, 5),
            "hallucination": False,
            "hallucination_reason": "None",
        })

    return json.dumps({"ready_for_triage": True, "follow_up_message": "", "gathered_context": "", "current_state": "ready"})


def _infer_duration(text: str) -> str | None:
    if "day" in text or "yesterday" in text:
        return "2 days"
    if "week" in text:
        return "1 week"
    if "hour" in text:
        return "3 hours"
    if "month" in text:
        return "2 weeks"
    return None


def _infer_severity(text: str) -> str | None:
    if "severe" in text or "extreme" in text or "worst" in text:
        return "severe"
    if "mild" in text or "little" in text or "slight" in text:
        return "mild"
    if "moderate" in text or "medium" in text:
        return "moderate"
    return None


def _vary_text(options: list[str], list_mode: bool = False):
    """Return one random option, or the full list shuffled if list_mode=True."""
    if list_mode:
        result = options.copy()
        random.shuffle(result)
        return result
    return random.choice(options)


# ── LangChain compatibility flag ──────────────────────────────────────────────
_LANGCHAIN_AVAILABLE = False
try:
    from langchain_core.language_models.chat_models import BaseChatModel
    from langchain_core.messages import BaseMessage, AIMessage, SystemMessage, HumanMessage
    from langchain_core.outputs import ChatGeneration, ChatResult
    from langchain_core.callbacks.manager import CallbackManagerForLLMRun
    _LANGCHAIN_AVAILABLE = True
except ImportError:
    logger.debug("langchain_core not installed — LangChain integration disabled")


def call(
    system_prompt: str,
    user_content: str,
    temperature: float | None = None,
    max_tokens: int = 500,
    timeout: float = 30.0,
) -> str:
    effective_temp = _get_temperature(system_prompt, temperature)

    if _MOCK_MODE:
        logger.warning("[MOCK] Returning simulated response (MOCK_MODE active)")
        return _mock_response(system_prompt, user_content)

    if not _API_KEY:
        raise ValueError(
            "TOGETHER_API_KEY environment variable not set. "
            "Set it or enable MOCK_MODE with GUARDIAN_ENV=development for testing."
        )

    payload = {
        "model": _MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_content},
        ],
        "temperature": effective_temp,
        "max_tokens": max_tokens,
    }

    start = time.time()
    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(
                _BASE,
                json=payload,
                headers={
                    "Authorization": f"Bearer {_API_KEY}",
                    "Content-Type": "application/json",
                },
            )
            resp.raise_for_status()
        data = resp.json()
    except Exception:
        raise

    elapsed = time.time() - start
    text = data["choices"][0]["message"]["content"]
    logger.debug("[Together] temp=%.2f response_length=%d latency=%.2fs", effective_temp, len(text), elapsed)
    return text.strip()


# ── LangChain ChatModel wrapper for Together.ai ───────────────────────────────

if _LANGCHAIN_AVAILABLE:
    class TogetherChatModel(BaseChatModel):
        """LangChain-compatible wrapper around the native Together.ai client."""

        model: str = _MODEL
        temperature: float = 0.3
        max_tokens: int = 500
        timeout: float = 30.0

        @property
        def _llm_type(self) -> str:
            return "together-chat"

        @property
        def _identifying_params(self) -> dict[str, Any]:
            return {
                "model": self.model,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
            }

        def _generate(
            self,
            messages: list[BaseMessage],
            stop: list[str] | None = None,
            run_manager: CallbackManagerForLLMRun | None = None,
            **kwargs: Any,
        ) -> ChatResult:
            system_prompt = ""
            user_content = ""
            for msg in messages:
                if isinstance(msg, SystemMessage):
                    system_prompt += msg.content + "\n"
                elif isinstance(msg, HumanMessage):
                    user_content += msg.content + "\n"
                elif isinstance(msg, AIMessage):
                    user_content += f"Assistant: {msg.content}\n"

            raw = call(
                system_prompt=system_prompt.strip(),
                user_content=user_content.strip(),
                temperature=kwargs.get("temperature", self.temperature),
                max_tokens=kwargs.get("max_tokens", self.max_tokens),
                timeout=kwargs.get("timeout", self.timeout),
            )
            message = AIMessage(content=raw)
            generation = ChatGeneration(message=message)
            return ChatResult(generations=[generation])

        async def _agenerate(
            self,
            messages: list[BaseMessage],
            stop: list[str] | None = None,
            run_manager: CallbackManagerForLLMRun | None = None,
            **kwargs: Any,
        ) -> ChatResult:
            import asyncio
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._generate, messages, stop, run_manager, **kwargs)


def get_langchain_llm(
    temperature: float = 0.3,
    max_tokens: int = 500,
    timeout: float = 30.0,
) -> Any:
    """Return a LangChain-compatible LLM instance.

    Falls back to a simple callable wrapper if langchain_core is not installed.
    """
    if _LANGCHAIN_AVAILABLE:
        return TogetherChatModel(
            model=_MODEL,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
        )
    class _SimpleLLM:
        async def ainvoke(self, prompt: str, **kwargs: Any) -> Any:
            lines = prompt.split("\n")
            system = ""
            user = ""
            in_system = False
            for line in lines:
                if line.lower().startswith("system:"):
                    in_system = True
                    system = line.split(":", 1)[1].strip()
                elif line.lower().startswith("user:") or line.lower().startswith("human:"):
                    in_system = False
                    user = line.split(":", 1)[1].strip()
                elif in_system:
                    system += "\n" + line
                else:
                    user += "\n" + line
            return call(system_prompt=system.strip(), user_content=user.strip(), **kwargs)
    return _SimpleLLM()
