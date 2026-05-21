"""
LangGraph node functions — thin wrappers around existing services.

Nodes catch failures, append to state.errors, and return safe partial updates
so the graph does not crash on a single step failure.
"""

from app.agents.state import AgentState
from app.services.bullet_critic import critique_bullets
from app.services.bullet_rewriter import rewrite_resume_bullets
from app.services.cover_letter_generator import (
    generate_cover_letter,
    generate_fallback_cover_letter,
)
from app.services.interview_prep_generator import (
    generate_fallback_interview_prep,
    generate_interview_prep,
)
from app.services.matcher import match_resume_to_jd
from app.services.report_generator import generate_report

# Maximum number of critique passes before we force-accept whatever we have.
# 1 retry = 2 total rewrite calls maximum.
_MAX_REWRITE_ATTEMPTS = 1


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
    """Step 2: Structured LLM bullet rewrite with fallback.

    On a retry pass, critique_feedback is already in state and gets forwarded
    to the prompt so the LLM knows exactly which issues to fix.
    """
    match_result = state.get("match_result") or _empty_match_result()
    # On first pass this is empty; on retry it holds the critique's issue list
    critique_feedback = state.get("critique_feedback") or []

    try:
        result = rewrite_resume_bullets(
            resume_text=state["resume_text"],
            jd_text=state["jd_text"],
            matched_skills=match_result["matched_skills"],
            missing_skills=match_result["missing_skills"],
            critique_feedback=critique_feedback or None,
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


def critique_node(state: AgentState) -> dict:
    """Step 3: LLM evaluates bullet quality and decides accept or retry.

    This is the core of the self-critique loop — the LLM's verdict controls
    whether rewrite_node runs again or the pipeline continues forward.
    Increments rewrite_attempts each pass so the loop is always finite.
    """
    bullets = state.get("rewritten_bullets") or []
    match_result = state.get("match_result") or _empty_match_result()

    # Track how many critique passes have run (used by route_after_critique)
    attempts = state.get("rewrite_attempts", 0) + 1

    try:
        critique, _ = critique_bullets(
            bullets=bullets,
            jd_text=state["jd_text"],
            resume_text=state["resume_text"],
            matched_skills=match_result["matched_skills"],
        )
        return {
            "rewrite_attempts": attempts,
            "critique_verdict": critique["verdict"],
            "critique_feedback": critique["issues"],
            "critique_score": critique["score"],
        }
    except Exception as exc:
        # Critique failure → force accept so the pipeline is never blocked
        return {
            "rewrite_attempts": attempts,
            "critique_verdict": "accept",
            "critique_feedback": [],
            "critique_score": 0,
            "errors": _merge_errors(state, [f"critique_node: {exc}"]),
        }


def route_after_critique(state: AgentState) -> str:
    """Routing function for the conditional edge after critique_node.

    Returns "rewrite" to loop back, or "cover_letter" to continue forward.
    The loop is capped at _MAX_REWRITE_ATTEMPTS to keep token cost predictable.

    Decision logic:
      - verdict == "retry" AND attempts <= cap  →  rewrite again
      - verdict == "accept" OR attempts > cap   →  continue to cover_letter
    """
    verdict = state.get("critique_verdict", "accept")
    attempts = state.get("rewrite_attempts", 0)

    if verdict == "retry" and attempts <= _MAX_REWRITE_ATTEMPTS:
        return "rewrite"
    return "cover_letter"


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


def interview_prep_node(state: AgentState) -> dict:
    """Step 4: LLM interview prep generation with fallback."""
    match_result = state.get("match_result") or _empty_match_result()

    try:
        prep, success = generate_interview_prep(
            resume_text=state["resume_text"],
            jd_text=state["jd_text"],
            matched_skills=match_result["matched_skills"],
            missing_skills=match_result["missing_skills"],
        )
        return {
            "technical_questions": prep["technical_questions"],
            "behavioral_questions": prep["behavioral_questions"],
            "study_topics": prep["study_topics"],
            "interview_prep_success": success,
        }
    except Exception as exc:
        # generate_interview_prep shouldn't raise, but catch anything unexpected
        fallback = generate_fallback_interview_prep(
            match_result["matched_skills"],
            match_result["missing_skills"],
        )
        return {
            "technical_questions": fallback["technical_questions"],
            "behavioral_questions": fallback["behavioral_questions"],
            "study_topics": fallback["study_topics"],
            "interview_prep_success": False,
            "errors": _merge_errors(state, [f"interview_prep_node: {exc}"]),
        }


def report_node(state: AgentState) -> dict:
    """Step 5: Markdown report from all prior node outputs (no LLM)."""
    match_result = state.get("match_result") or _empty_match_result()
    bullets = state.get("rewritten_bullets") or []
    llm_success = state.get("llm_success", True)
    cover_letter = state.get("cover_letter", "")
    cover_letter_success = state.get("cover_letter_success", True)
    technical_questions = state.get("technical_questions") or []
    behavioral_questions = state.get("behavioral_questions") or []
    study_topics = state.get("study_topics") or []
    interview_prep_success = state.get("interview_prep_success", True)

    try:
        final_report = generate_report(
            match_result,
            bullets,
            llm_success=llm_success,
            cover_letter=cover_letter,
            cover_letter_success=cover_letter_success,
            technical_questions=technical_questions,
            behavioral_questions=behavioral_questions,
            study_topics=study_topics,
            interview_prep_success=interview_prep_success,
        )
        return {"final_report": final_report}
    except Exception as exc:
        return {
            "final_report": "# Job Match Report\n\nReport generation failed.",
            "errors": _merge_errors(state, [f"report_node: {exc}"]),
        }
