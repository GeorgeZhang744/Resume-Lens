"""
LangGraph workflow definition for resume–JD analysis.

Flow:
  START → match_node → rewrite_node → cover_letter_node → report_node → END
"""

from langgraph.graph import END, START, StateGraph

from app.agents.nodes import cover_letter_node, match_node, report_node, rewrite_node
from app.agents.state import AgentState


def build_graph():
    """
    Build and compile the analyze workflow graph.

    Returns a compiled graph with .invoke(initial_state).
    """
    workflow = StateGraph(AgentState)

    # Register nodes (each wraps one service call)
    workflow.add_node("match", match_node)
    workflow.add_node("rewrite", rewrite_node)
    workflow.add_node("cover_letter", cover_letter_node)
    workflow.add_node("report", report_node)

    # Linear pipeline
    workflow.add_edge(START, "match")
    workflow.add_edge("match", "rewrite")
    workflow.add_edge("rewrite", "cover_letter")
    workflow.add_edge("cover_letter", "report")
    workflow.add_edge("report", END)

    return workflow.compile()


# Single compiled instance reused by the API (avoids recompiling per request)
analyze_graph = build_graph()
