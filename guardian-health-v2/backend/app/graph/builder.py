"""
Graph Builder — Constructs the complete LangGraph StateGraph for triage.

Pipeline:
  input_gate → firewall → privacy → extractor → ml_predictor → reasoner →
  [consultation | triage | disease_info | emergency] →
  compliance → assembler → persist → END

All conditional routing is defined here.
"""


import logging
from typing import Any

from langgraph.graph import END, StateGraph

from app.graph.nodes.consultation import consultation_node
from app.graph.nodes.extraction import extractor_node, ml_predictor_node
from app.graph.nodes.postprocess import assembler_node, compliance_node, persist_node
from app.graph.nodes.preprocess import firewall_node, input_gate_node, privacy_node
from app.graph.nodes.reasoning import reasoner_node
from app.graph.nodes.triage import diagnosed_info_node, emergency_node, triage_node
from app.graph.state import TriageState

logger = logging.getLogger("guardian.graph")

# ---------------------------------------------------------------------------
# Conditional routing functions
# ---------------------------------------------------------------------------

def route_after_firewall(state: TriageState) -> str:
    """Route after firewall: medical queries go to privacy, non-medical are rejected."""
    if state.get("is_emergency"):
        logger.info("Routing: emergency detected -> emergency node")
        return "emergency"
    if not state.get("is_medical", True):
        logger.info("Routing: non-medical query -> END (rejected)")
        return "assembler"  # Will assemble rejection response
    logger.info("Routing: medical query -> privacy")
    return "privacy"


def route_after_extractor(state: TriageState) -> str:
    """Route after extraction and ML prediction to reasoning."""
    if state.get("is_emergency"):
        return "emergency"
    return "reasoner"


def route_after_reasoner(state: TriageState) -> str:
    """
    Route after reasoner based on confidence and context.

    - High confidence + symptoms -> triage
    - Medium confidence -> consultation
    - Disease info query pattern -> disease_info
    - Emergency flagged -> emergency
    """
    if state.get("is_emergency"):
        return "emergency"

    confidence = state.get("reasoning_confidence", 0.5)
    symptoms = state.get("symptoms", [])
    user_input = state.get("user_input", "").lower()

    # Check for disease info intent
    disease_info_keywords = [
        "what is", "what are", "tell me about", "information about",
        "explain", "overview of", "details about",
    ]
    is_disease_query = any(kw in user_input for kw in disease_info_keywords) and len(symptoms) <= 1

    if is_disease_query and confidence < 0.6:
        logger.info("Routing: disease info query -> disease_info")
        return "disease_info"

    if confidence >= 0.6 and symptoms:
        logger.info("Routing: confident triage -> triage")
        return "triage"

    logger.info("Routing: consultation path (confidence=%.2f)", confidence)
    return "consultation"


def route_after_processing(state: TriageState) -> str:
    """All processing nodes converge to compliance."""
    return "compliance"


def route_after_compliance(state: TriageState) -> str:
    """Route after compliance: approved -> assembler, blocked -> assembler (with block note)."""
    return "assembler"


def should_continue_after_assembler(state: TriageState) -> str:
    """After assembly, persist then end."""
    if state.get("error"):
        return "persist"  # Still try to persist error state
    return "persist"


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------

_graph_instance: Any = None


def build_graph() -> StateGraph:
    """Build and return the complete triage StateGraph."""
    workflow = StateGraph(TriageState)

    # ---- Register all nodes ----
    workflow.add_node("input_gate", input_gate_node)
    workflow.add_node("firewall", firewall_node)
    workflow.add_node("privacy", privacy_node)
    workflow.add_node("extractor", extractor_node)
    workflow.add_node("ml_predictor", ml_predictor_node)
    workflow.add_node("reasoner", reasoner_node)
    workflow.add_node("consultation", consultation_node)
    workflow.add_node("triage", triage_node)
    workflow.add_node("disease_info", diagnosed_info_node)
    workflow.add_node("emergency", emergency_node)
    workflow.add_node("compliance", compliance_node)
    workflow.add_node("assembler", assembler_node)
    workflow.add_node("persist", persist_node)

    # ---- Define edges ----
    workflow.set_entry_point("input_gate")

    # Input gate always goes to firewall
    workflow.add_edge("input_gate", "firewall")

    # Firewall conditional routing
    workflow.add_conditional_edges(
        "firewall",
        route_after_firewall,
        {
            "privacy": "privacy",
            "emergency": "emergency",
            "assembler": "assembler",
        },
    )

    # Privacy -> extractor
    workflow.add_edge("privacy", "extractor")

    # Extractor -> ml_predictor (sequential in same "pass")
    workflow.add_edge("extractor", "ml_predictor")

    # ML predictor -> reasoner
    workflow.add_edge("ml_predictor", "reasoner")

    # Reasoner conditional routing
    workflow.add_conditional_edges(
        "reasoner",
        route_after_reasoner,
        {
            "consultation": "consultation",
            "triage": "triage",
            "disease_info": "disease_info",
            "emergency": "emergency",
        },
    )

    # All processing nodes -> compliance
    workflow.add_edge("consultation", "compliance")
    workflow.add_edge("triage", "compliance")
    workflow.add_edge("disease_info", "compliance")
    workflow.add_edge("emergency", "compliance")

    # Compliance -> assembler
    workflow.add_edge("compliance", "assembler")

    # Assembler -> persist
    workflow.add_edge("assembler", "persist")

    # Persist -> END
    workflow.add_edge("persist", END)

    logger.info("Triage graph built with %d nodes", len(workflow.nodes))
    return workflow.compile()


def get_triage_graph() -> Any:
    """Get or create the singleton compiled graph."""
    global _graph_instance
    if _graph_instance is None:
        _graph_instance = build_graph()
        logger.info("Triage graph singleton initialized")
    return _graph_instance


def reset_graph() -> None:
    """Reset the graph singleton (useful for testing)."""
    global _graph_instance
    _graph_instance = None
    logger.info("Triage graph singleton reset")
