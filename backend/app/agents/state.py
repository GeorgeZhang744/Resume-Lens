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
    Reliability: llm_success, errors
    """

    # Inputs (set by API route before invoke)
    resume_text: str
    jd_text: str

    # Outputs (set step by step)
    match_result: MatchResult
    rewritten_bullets: list[str]
    cover_letter: str
    technical_questions: list[str]
    behavioral_questions: list[str]
    study_topics: list[str]
    final_report: str

    # Self-critique loop
    rewrite_attempts: int       # how many critique passes have run (caps the retry loop)
    critique_verdict: str       # "accept" or "retry" — drives conditional routing
    critique_feedback: list[str]  # specific issues passed back into the rewrite prompt
    critique_score: int         # 1–10 quality score (0 = critique call failed)

    # Reliability tracking
    llm_success: bool
    cover_letter_success: bool
    interview_prep_success: bool
    errors: list[str]
