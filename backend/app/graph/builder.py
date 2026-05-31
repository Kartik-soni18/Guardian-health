"""Assemble the LangGraph StateGraph for GuardianHealth triage."""

import logging

from langgraph.graph import StateGraph, END

from app.graph.state import TriageState
from app.graph.nodes import (
    input_gate_node,
    firewall_node,
    privacy_node,
    extractor_node,
    ml_predictor_node,
    reasoner_node,
    consultation_node,
    triage_node,
    diagnosed_info_node,
    compliance_node,
    assembler_node,
    persist_node,
)

logger = logging.getLogger(__name__)


def build_graph():
    """Build and compile the triage StateGraph."""
    builder = StateGraph(TriageState)

    # ── Nodes ────────────────────────────────────────────────────────────────
    builder.add_node("input_gate", input_gate_node)
    builder.add_node("firewall", firewall_node)
    builder.add_node("privacy", privacy_node)
    builder.add_node("extractor", extractor_node)
    builder.add_node("ml_predictor", ml_predictor_node)
    builder.add_node("reasoner", reasoner_node)
    builder.add_node("consultation", consultation_node)
    builder.add_node("triage", triage_node)
    builder.add_node("diagnosed_info", diagnosed_info_node)
    builder.add_node("compliance", compliance_node)
    builder.add_node("assembler", assembler_node)
    builder.add_node("persist", persist_node)

    # ── Edges ────────────────────────────────────────────────────────────────
    builder.set_entry_point("input_gate")

    builder.add_conditional_edges(
        "input_gate",
        _route_after_input_gate,
        {
            "valid": "firewall",
            "invalid": END,
        },
    )

    builder.add_conditional_edges(
        "firewall",
        _route_after_firewall,
        {
            "medical": "privacy",
            "rejected": END,
        },
    )

    builder.add_edge("privacy", "extractor")
    builder.add_edge("extractor", "ml_predictor")
    builder.add_edge("ml_predictor", "reasoner")

    builder.add_conditional_edges(
        "reasoner",
        _route_after_reasoner,
        {
            "emergency": "assembler",
            "diagnosed": "diagnosed_info",
            "consultation": "consultation",
        },
    )

    builder.add_conditional_edges(
        "consultation",
        _route_after_consultation,
        {
            "ready": "triage",
            "follow_up": "assembler",
        },
    )

    builder.add_edge("diagnosed_info", "compliance")
    builder.add_edge("compliance", "assembler")
    builder.add_edge("triage", "assembler")
    builder.add_edge("assembler", "persist")
    builder.add_edge("persist", END)

    return builder.compile()


# ── Conditional edge functions ───────────────────────────────────────────────

def _route_after_input_gate(state: TriageState) -> str:
    if state.get("error"):
        return "invalid"
    return "valid"


def _route_after_firewall(state: TriageState) -> str:
    if state.get("status") == "rejected":
        return "rejected"
    return "medical"


def _route_after_reasoner(state: TriageState) -> str:
    if state.get("emergency_detected"):
        return "emergency"
    final_routing = state.get("final_routing", "consultation")
    if final_routing == "diagnosed":
        return "diagnosed"
    return "consultation"


def _route_after_consultation(state: TriageState) -> str:
    consultation = state.get("consultation_result", {})
    if consultation.get("ready_for_triage"):
        return "ready"
    return "follow_up"
