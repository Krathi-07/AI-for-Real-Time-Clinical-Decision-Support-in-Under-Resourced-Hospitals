# src/agent/graph.py
from langgraph.graph import END, StateGraph

from src.agent.nodes import (
    fusion_node,
    nlp_node,
    summary_node,
    triage_node,
    vitals_node,
)
from src.agent.state import AgentState


def _route_after_triage(state: AgentState) -> str:
    """
    Conditional edge after triage.
    If data is sufficient, proceed to vitals analysis.
    If not, jump straight to summary which will compose an abstention alert.
    """
    if state.get("data_sufficient", False):
        return "vitals_node"
    return "summary_node"


def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    # Register nodes
    graph.add_node("triage_node", triage_node)
    graph.add_node("vitals_node", vitals_node)
    graph.add_node("nlp_node", nlp_node)
    graph.add_node("fusion_node", fusion_node)
    graph.add_node("summary_node", summary_node)

    # Entry point
    graph.set_entry_point("triage_node")

    # Conditional branch after triage
    graph.add_conditional_edges(
        "triage_node",
        _route_after_triage,
        {
            "vitals_node": "vitals_node",
            "summary_node": "summary_node",
        }
    )

    # Linear path through the rest
    graph.add_edge("vitals_node", "nlp_node")
    graph.add_edge("nlp_node", "fusion_node")
    graph.add_edge("fusion_node", "summary_node")
    graph.add_edge("summary_node", END)

    return graph.compile()


# Module-level compiled graph — import this in the API and smoke test
clinical_agent = build_graph()