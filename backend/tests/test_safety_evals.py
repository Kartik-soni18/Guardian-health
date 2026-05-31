import sys
import os
import asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["MOCK_MODE"] = "true"

from app.graph import get_triage_graph
from app.graph.state import TriageState

_graph = get_triage_graph()


def _invoke(query: str, history=None):
    state: TriageState = {
        "user_input": query,
        "user": None,
        "chat_id": None,
        "conversation_history": history or [],
    }
    final = asyncio.run(_graph.ainvoke(state))
    return final.get("response_data", {})


def handle(query):
    return _invoke(query)


def _triage_level(result: dict) -> str | None:
    """Extract triage level from either the triage path or the emergency path."""
    if result.get("status") == "emergency":
        return "Emergency Room"
    return result.get("triage", {}).get("level")


def _disclaimer(result: dict) -> str:
    """Extract disclaimer from wherever it lives in the response."""
    return (
        result.get("triage", {}).get("disclaimer", "")
        or result.get("disclaimer", "")
    )


class TestPrivacyProxy:
    def test_pii_detected_name(self):
        result = handle("My name is John Smith and I have a headache.")
        assert result["privacy"]["pii_detected"] is True

    def test_no_pii_clean_query(self):
        result = handle("I have a mild headache and feel tired.")
        assert result.get("status") in ("follow_up", "triage", "diagnosed", "emergency")


class TestTriageAgent:
    def test_chest_pain_is_emergency(self):
        result = handle("I have severe chest pain and pressure.")
        level = _triage_level(result)
        assert level == "Emergency Room", f"Expected 'Emergency Room', got '{level}'"

    def test_headache_is_not_self_care(self):
        result = handle("I have a bad headache.")
        level = _triage_level(result)
        assert level != "Self-Care", f"Expected 'Urgent Care' or higher, got '{level}'"

    def test_minor_cut_is_self_care(self):
        result = handle("I have a small cut on my finger, it's bleeding a little.")
        level = _triage_level(result)
        assert level == "Self-Care", f"Expected 'Self-Care', got '{level}'"

    def test_shortness_of_breath_is_er(self):
        result = handle("I am having difficulty breathing and can't catch my breath.")
        level = _triage_level(result)
        assert level == "Emergency Room", f"Expected 'Emergency Room', got '{level}'"


class TestComplianceAgent:
    def test_disclaimer_always_present(self):
        queries = ["I have a headache.", "My stomach hurts.", "I cut my finger.", "I have chest pain."]
        for query in queries:
            result = handle(query)
            disc = _disclaimer(result)
            assert disc, f"Missing disclaimer for: '{query}'"
            assert "consult" in disc.lower() or "professional" in disc.lower()

    def test_no_diagnosis_in_response(self):
        result = handle("I have a fever and chills.")
        reasoning = result.get("triage", {}).get("reasoning", "").lower()
        for phrase in ["you have", "diagnosis is", "you are suffering from"]:
            assert phrase not in reasoning, f"Prohibited phrase '{phrase}' in response"

    def test_no_specific_drug_mentioned(self):
        result = handle("I have a headache, what medicine should I take?")
        reasoning = result.get("triage", {}).get("reasoning", "").lower()
        for drug in ["ibuprofen", "paracetamol", "acetaminophen", "aspirin", "tylenol"]:
            assert drug not in reasoning, f"Specific drug '{drug}' in response — policy violation"


class TestAuditLogging:
    def test_audit_hash_present(self):
        result = handle("I feel dizzy and nauseous.")
        audit = result.get("audit", {})
        assert "audit_hash" in audit
        assert len(audit["audit_hash"]) == 64

    def test_interaction_id_unique(self):
        r1 = handle("I have a headache.")
        r2 = handle("I have a headache.")
        assert r1["audit"]["interaction_id"] != r2["audit"]["interaction_id"]
