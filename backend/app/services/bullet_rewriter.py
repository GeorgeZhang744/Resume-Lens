"""
AI-powered resume bullet rewriting (single LLM call per analyze request).

Rule-based matching stays in matcher.py — this module only rewrites bullets.
"""

import re

from app.prompts.bullet_rewrite_prompt import (
    SYSTEM_PROMPT,
    build_bullet_rewrite_prompt,
)
from app.services.llm_service import generate_text

# Matches: "- bullet 1", "- bullet 1: text", "- text"
_BULLET_LINE = re.compile(
    r"^[-*]\s*(?:bullet\s*\d+\s*[:\-.]?\s*)?(.+)$",
    re.IGNORECASE,
)
_BULLET_PREFIX = re.compile(r"^bullet\s*\d+\s*[:\-.]?\s*", re.IGNORECASE)


def _clean_bullet_text(text: str) -> str:
    """Strip leftover 'bullet 1:' labels from captured text."""
    cleaned = _BULLET_PREFIX.sub("", text).strip()
    return cleaned or text.strip()


def _parse_bullets(raw_response: str) -> list[str]:
    """
    Parse LLM output into a list of bullet strings.

    Expected format:
    - bullet 1
    - bullet 2
    """
    bullets: list[str] = []

    for line in raw_response.splitlines():
        line = line.strip()
        if not line:
            continue

        match = _BULLET_LINE.match(line)
        if match:
            text = _clean_bullet_text(match.group(1))
            if text and not re.fullmatch(r"bullet\s*\d+", text, re.I):
                bullets.append(text)
            continue

        # Fallback: numbered list "1. text"
        numbered = re.match(r"^\d+[\.\)]\s+(.+)$", line)
        if numbered:
            bullets.append(numbered.group(1).strip())

    # Last resort: use non-empty lines if model ignored format
    if not bullets:
        bullets = [line.strip() for line in raw_response.splitlines() if line.strip()]

    return bullets[:5]


def _fallback_bullets(
    matched_skills: list[str],
    missing_skills: list[str],
) -> list[str]:
    """Simple templates if the LLM call fails (keeps the API usable)."""
    bullets: list[str] = []
    if matched_skills:
        skills = ", ".join(matched_skills[:3])
        bullets.append(
            f"Highlighted {skills} experience aligned with the target role requirements."
        )
    if missing_skills:
        gaps = ", ".join(missing_skills[:3])
        bullets.append(
            f"Strengthen resume examples demonstrating {gaps} where accurate experience exists."
        )
    if not bullets:
        bullets.append(
            "Add quantified, action-oriented bullets that mirror keywords from the job description."
        )
    return bullets[:3]


def rewrite_resume_bullets(
    resume_text: str,
    jd_text: str,
    matched_skills: list[str],
    missing_skills: list[str],
) -> list[str]:
    """
    Rewrite resume bullets via one OpenAI call.

    Workflow:
    1. build_bullet_rewrite_prompt() → user message
    2. generate_text() → raw LLM response
    3. _parse_bullets() → list[str]
    """
    user_prompt = build_bullet_rewrite_prompt(
        resume_text=resume_text,
        jd_text=jd_text,
        matched_skills=matched_skills,
        missing_skills=missing_skills,
    )

    try:
        raw = generate_text(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            temperature=0.3,
        )
        bullets = _parse_bullets(raw)
        if bullets:
            return bullets
    except (ValueError, RuntimeError):
        # Missing key or API error — return safe fallback bullets
        pass

    return _fallback_bullets(matched_skills, missing_skills)
