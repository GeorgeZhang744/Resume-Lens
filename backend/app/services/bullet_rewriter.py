"""
AI-powered resume bullet rewriting (single structured LLM call per analyze).

Returns bullets plus llm_success / errors for LangGraph state tracking.
"""

from typing import TypedDict

from pydantic import ValidationError

from app.api.schemas import BulletRewriteResponse
from app.prompts.bullet_rewrite_prompt import (
    SYSTEM_PROMPT,
    build_bullet_rewrite_prompt,
)
from app.services.llm_service import LLMServiceError, generate_json


class RewriteBulletsResult(TypedDict):
    """Result passed from rewrite service to the LangGraph rewrite node."""

    rewritten_bullets: list[str]
    llm_success: bool
    errors: list[str]


def generate_fallback_bullets(
    matched_skills: list[str],
    missing_skills: list[str],
) -> list[str]:
    """
    Professional template bullets when the LLM or validation fails.

    Still references real matched/missing skills from rule-based matching.
    """
    bullets: list[str] = []

    if matched_skills:
        lead = ", ".join(matched_skills[:3])
        bullets.append(
            f"Delivered production features using {lead}, directly aligning with "
            "the role's core technical requirements."
        )
        if len(matched_skills) >= 2:
            bullets.append(
                f"Applied {matched_skills[0]} and {matched_skills[1]} to ship "
                "reliable solutions with measurable impact on team delivery goals."
            )

    if missing_skills:
        gaps = ", ".join(missing_skills[:3])
        bullets.append(
            f"Where accurate, expand resume examples highlighting {gaps} "
            "to improve ATS match and interview relevance."
        )

    if not bullets:
        bullets.append(
            "Translate job-description keywords into quantified, action-oriented "
            "bullets grounded in your actual project experience."
        )

    return bullets[:3]


def rewrite_resume_bullets(
    resume_text: str,
    jd_text: str,
    matched_skills: list[str],
    missing_skills: list[str],
    critique_feedback: list[str] | None = None,
) -> RewriteBulletsResult:
    """
    Rewrite bullets via structured JSON + Pydantic validation.

    critique_feedback: issues from a previous critique pass injected into the
    prompt so the LLM knows exactly what to fix on a retry attempt.

    On API, JSON, or validation failure → fallback bullets, llm_success=False.
    """
    errors: list[str] = []
    user_prompt = build_bullet_rewrite_prompt(
        resume_text=resume_text,
        jd_text=jd_text,
        matched_skills=matched_skills,
        missing_skills=missing_skills,
        critique_feedback=critique_feedback,
    )

    try:
        raw_json = generate_json(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            temperature=0.3,
        )
        validated = BulletRewriteResponse.model_validate(raw_json)
        return {
            "rewritten_bullets": validated.rewritten_bullets,
            "llm_success": True,
            "errors": [],
        }
    except ValidationError as exc:
        errors.append(f"Schema validation failed: {exc}")
    except LLMServiceError as exc:
        errors.append(str(exc))
    except ValueError as exc:
        errors.append(f"Configuration error: {exc}")
    except Exception as exc:
        errors.append(f"Unexpected rewrite error: {exc}")

    return {
        "rewritten_bullets": generate_fallback_bullets(
            matched_skills, missing_skills
        ),
        "llm_success": False,
        "errors": errors,
    }
