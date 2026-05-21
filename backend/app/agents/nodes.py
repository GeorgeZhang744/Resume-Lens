"""
LangGraph node functions — thin wrappers around existing services.

Business logic stays in services/; nodes only call services and update state.
"""

from app.agents.state import AgentState
from app.services.bullet_rewriter import rewrite_resume_bullets
from app.services.matcher import match_resume_to_jd
from app.services.report_generator import generate_report


def match_node(state: AgentState) -> dict:
    """
    Step 1: Rule-based skill matching (no LLM).
    """
    match_result = match_resume_to_jd(
        resume_text=state["resume_text"],
        jd_text=state["jd_text"],
    )
    return {"match_result": match_result}


def rewrite_node(state: AgentState) -> dict:
    """
    Step 2: AI bullet rewriting (single LLM call).
    """
    match_result = state["match_result"]
    rewritten_bullets = rewrite_resume_bullets(
        resume_text=state["resume_text"],
        jd_text=state["jd_text"],
        matched_skills=match_result["matched_skills"],
        missing_skills=match_result["missing_skills"],
    )
    return {"rewritten_bullets": rewritten_bullets}


def report_node(state: AgentState) -> dict:
    """
    Step 3: Markdown report from match + bullets (no LLM).
    """
    final_report = generate_report(
        state["match_result"],
        state["rewritten_bullets"],
    )
    return {"final_report": final_report}
