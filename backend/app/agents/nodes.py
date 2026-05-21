"""
LangGraph node functions — thin wrappers around existing services.

Nodes catch failures, append to state.errors, and return safe partial updates
so the graph does not crash on a single step failure.
"""

from app.agents.state import AgentState
from app.services.bullet_rewriter import rewrite_resume_bullets
from app.services.cover_letter_generator import (
    generate_cover_letter,
    generate_fallback_cover_letter,
)
from app.services.matcher import match_resume_to_jd
from app.services.report_generator import generate_report


def _merge_errors(state: AgentState, new_errors: list[str]) -> list[str]:
    """Append new error messages to any existing ones in state."""
    existing = list(state.get("errors") or [])
    return existing + new_errors


def _empty_match_result() -> dict:
    """Safe default when match_node fails."""
    return {
        "match_score": 0,
        "matched_skills": [],
        "missing_skills": [],
        "resume_skills": [],
        "jd_skills": [],
    }


def match_node(state: AgentState) -> dict:
    """Step 1: Rule-based skill matching (no LLM)."""
    try:
        match_result = match_resume_to_jd(
            resume_text=state["resume_text"],
            jd_text=state["jd_text"],
        )
        return {"match_result": match_result}
    except Exception as exc:
        return {
            "match_result": _empty_match_result(),
            "errors": _merge_errors(state, [f"match_node: {exc}"]),
        }


def rewrite_node(state: AgentState) -> dict:
    """Step 2: Structured LLM bullet rewrite with fallback."""
    match_result = state.get("match_result") or _empty_match_result()

    try:
        result = rewrite_resume_bullets(
            resume_text=state["resume_text"],
            jd_text=state["jd_text"],
            matched_skills=match_result["matched_skills"],
            missing_skills=match_result["missing_skills"],
        )
        update: dict = {
            "rewritten_bullets": result["rewritten_bullets"],
            "llm_success": result["llm_success"],
        }
        if result["errors"]:
            update["errors"] = _merge_errors(state, result["errors"])
        return update
    except Exception as exc:
        from app.services.bullet_rewriter import generate_fallback_bullets

        return {
            "rewritten_bullets": generate_fallback_bullets(
                match_result["matched_skills"],
                match_result["missing_skills"],
            ),
            "llm_success": False,
            "errors": _merge_errors(state, [f"rewrite_node: {exc}"]),
        }


def cover_letter_node(state: AgentState) -> dict:
    """Step 3: LLM cover letter generation with fallback."""
    match_result = state.get("match_result") or _empty_match_result()

    try:
        cover_letter, success = generate_cover_letter(
            resume_text=state["resume_text"],
            jd_text=state["jd_text"],
            matched_skills=match_result["matched_skills"],
            missing_skills=match_result["missing_skills"],
        )
        return {
            "cover_letter": cover_letter,
            "cover_letter_success": success,
        }
    except Exception as exc:
        # generate_cover_letter shouldn't raise, but catch anything unexpected
        return {
            "cover_letter": generate_fallback_cover_letter(
                match_result["matched_skills"],
                match_result["missing_skills"],
            ),
            "cover_letter_success": False,
            "errors": _merge_errors(state, [f"cover_letter_node: {exc}"]),
        }


def report_node(state: AgentState) -> dict:
    """Step 4: Markdown report from match + bullets + cover letter (no LLM)."""
    match_result = state.get("match_result") or _empty_match_result()
    bullets = state.get("rewritten_bullets") or []
    llm_success = state.get("llm_success", True)
    cover_letter = state.get("cover_letter", "")
    cover_letter_success = state.get("cover_letter_success", True)

    try:
        final_report = generate_report(
            match_result,
            bullets,
            llm_success=llm_success,
            cover_letter=cover_letter,
            cover_letter_success=cover_letter_success,
        )
        return {"final_report": final_report}
    except Exception as exc:
        return {
            "final_report": "# Job Match Report\n\nReport generation failed.",
            "errors": _merge_errors(state, [f"report_node: {exc}"]),
        }
