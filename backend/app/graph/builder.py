"""LangGraph StateGraph for triage — LLM-only pipeline (no ML)."""

import logging
from typing import Any

from langgraph.graph import END, StateGraph

from app.graph.nodes.consultation import consultation_node
from app.graph.nodes.dataset_lookup import dataset_lookup_node
from app.graph.nodes.extraction import extractor_node
from app.graph.nodes.postprocess import assembler_node, compliance_node, persist_node
from app.graph.nodes.preprocess import firewall_node, input_gate_node, privacy_node
from app.graph.nodes.reasoning import reasoner_node
from app.graph.nodes.triage import diagnosed_info_node, emergency_node, triage_node
from app.graph.state import TriageState

logger = logging.getLogger("guardian.graph")


def route_after_firewall(state: TriageState) -> str:
    if state.get("is_emergency"):
        return "emergency"
    if not state.get("is_medical", True):
        return "assembler"
    return "privacy"


def route_after_reasoner(state: TriageState) -> str:
    if state.get("is_emergency"):
        return "emergency"

    confidence = state.get("reasoning_confidence", 0.5)
    symptoms = state.get("symptoms", [])
    user_input = state.get("user_input", "").lower()

    disease_info_keywords = [
        "what is", "what are", "tell me about", "information about",
        "explain", "overview of", "details about",
    ]
    is_disease_query = any(kw in user_input for kw in disease_info_keywords) and len(symptoms) <= 1

    if is_disease_query and confidence < 0.6:
        return "disease_info"
    if confidence >= 0.6 and symptoms:
        return "triage"
    return "consultation"


_graph_instance: Any = None


def build_graph() -> StateGraph:
    workflow = StateGraph(TriageState)

    workflow.add_node("input_gate", input_gate_node)
    workflow.add_node("firewall", firewall_node)
    workflow.add_node("privacy", privacy_node)
    workflow.add_node("extractor", extractor_node)
    workflow.add_node("dataset_lookup", dataset_lookup_node)
    workflow.add_node("reasoner", reasoner_node)
    workflow.add_node("consultation", consultation_node)
    workflow.add_node("triage", triage_node)
    workflow.add_node("disease_info", diagnosed_info_node)
    workflow.add_node("emergency", emergency_node)
    workflow.add_node("compliance", compliance_node)
    workflow.add_node("assembler", assembler_node)
    workflow.add_node("persist", persist_node)

    workflow.set_entry_point("input_gate")
    workflow.add_edge("input_gate", "firewall")
    workflow.add_conditional_edges(
        "firewall",
        route_after_firewall,
        {"privacy": "privacy", "emergency": "emergency", "assembler": "assembler"},
    )
    workflow.add_edge("privacy", "extractor")
    workflow.add_edge("extractor", "dataset_lookup")
    workflow.add_edge("dataset_lookup", "reasoner")
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
    workflow.add_edge("consultation", "compliance")
    workflow.add_edge("triage", "compliance")
    workflow.add_edge("disease_info", "compliance")
    workflow.add_edge("emergency", "compliance")
    workflow.add_edge("compliance", "assembler")
    workflow.add_edge("assembler", "persist")
    workflow.add_edge("persist", END)

    return workflow.compile()


def get_triage_graph() -> Any:
    global _graph_instance
    if _graph_instance is None:
        _graph_instance = build_graph()
    return _graph_instance


def reset_graph() -> None:
    global _graph_instance
    _graph_instance = None
