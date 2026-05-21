"""
LLM-based skill extraction and resume–JD matching.

Replaces the previous rule-based keyword scanner.

Why LLM?
- No fixed vocabulary: works for any tech stack, not just the 32 skills we
  hand-coded before.
- Semantic matching: "ML" on a resume correctly matches "Machine Learning" in
  the JD without an alias table.
- Normalisation is automatic: the model returns consistent display names
  regardless of how the candidate wrote them.

Fallback:
  If the LLM call or JSON parsing fails, an empty MatchResult is returned so
  the rest of the agent pipeline can still proceed gracefully.
"""

import logging
from typing import TypedDict

from app.prompts.matcher_prompt import SYSTEM_PROMPT, build_matcher_prompt
from app.services.llm_service import LLMServiceError, generate_json

logger = logging.getLogger(__name__)


class MatchResult(TypedDict):
    """Structured output from match_resume_to_jd."""

    match_score: int
    matched_skills: list[str]
    missing_skills: list[str]
    resume_skills: list[str]
    jd_skills: list[str]


def _safe_str_list(value: object) -> list[str]:
    """Coerce a JSON value to a flat list of non-empty strings."""
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if item]


def _fallback_match() -> MatchResult:
    """Safe empty result returned when the LLM call fails."""
    return {
        "match_score": 0,
        "matched_skills": [],
        "missing_skills": [],
        "resume_skills": [],
        "jd_skills": [],
    }


def match_resume_to_jd(resume_text: str, jd_text: str) -> MatchResult:
    """
    Compare resume skills to job-description skills using an LLM.

    A single GPT call extracts, normalises, and semantically matches all
    technical skills from both documents. The match_score is recomputed
    server-side to guard against model arithmetic errors.

    Returns a MatchResult with safe defaults if the LLM call fails.
    """
    try:
        data = generate_json(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=build_matcher_prompt(resume_text, jd_text),
            temperature=0.0,  # deterministic extraction
        )
    except (LLMServiceError, ValueError) as exc:
        logger.warning("LLM skill extraction failed — returning empty result: %s", exc)
        return _fallback_match()

    resume_skills  = _safe_str_list(data.get("resume_skills"))
    jd_skills      = _safe_str_list(data.get("jd_skills"))
    matched_skills = _safe_str_list(data.get("matched_skills"))
    missing_skills = _safe_str_list(data.get("missing_skills"))

    # Recompute score server-side — don't trust LLM arithmetic
    total_jd   = len(jd_skills)
    match_score = round(len(matched_skills) / total_jd * 100) if total_jd else 0

    return {
        "match_score":    match_score,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "resume_skills":  resume_skills,
        "jd_skills":      jd_skills,
    }
