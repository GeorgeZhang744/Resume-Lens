"""
Shared state passed between LangGraph nodes.

Each node reads from state and returns a partial update (dict)
that LangGraph merges into the full state.
"""

from typing import TypedDict

from app.services.matcher import MatchResult


class AgentState(TypedDict, total=False):
    """
    Workflow state for POST /api/analyze.

    Required inputs: resume_text, jd_text
    Filled by nodes: match_result, rewritten_bullets, final_report
    """

    # Inputs (set by API route before invoke)
    resume_text: str
    jd_text: str

    # Outputs (set step by step)
    match_result: MatchResult
    rewritten_bullets: list[str]
    final_report: str

    # Optional: collect non-fatal issues from nodes
    errors: list[str]
