"""
AI-powered cover letter generation (single structured LLM call per analyze).

Returns the cover letter text plus a success flag for LangGraph state tracking.
"""

from pydantic import ValidationError

from app.api.schemas import CoverLetterResponse
from app.prompts.cover_letter_prompt import SYSTEM_PROMPT, build_cover_letter_prompt
from app.services.llm_service import LLMServiceError, generate_json


def generate_fallback_cover_letter(
    matched_skills: list[str],
    missing_skills: list[str],
) -> str:
    """
    Template cover letter when the LLM or validation fails.

    Still references real matched/missing skills from rule-based matching
    so the output is always grounded in something real.
    """
    matched_str = (
        ", ".join(matched_skills[:3]) if matched_skills else "relevant technical skills"
    )
    missing_str = (
        ", ".join(missing_skills[:2]) if missing_skills else "additional areas"
    )

    return (
        f"I am excited to apply for this position, where my background aligns well "
        f"with the role's core requirements. My experience with {matched_str} positions "
        f"me to contribute effectively from day one.\n\n"
        f"Throughout my career I have delivered results by applying these skills to "
        f"real-world challenges, working collaboratively with cross-functional teams, "
        f"and maintaining a strong focus on quality and measurable impact.\n\n"
        f"I am also actively developing my knowledge in {missing_str}, and I look "
        f"forward to growing in these areas within your organization.\n\n"
        f"I am enthusiastic about the opportunity to bring my skills to your team and "
        f"contribute to your goals. Thank you for considering my application."
    )


def generate_cover_letter(
    resume_text: str,
    jd_text: str,
    matched_skills: list[str],
    missing_skills: list[str],
) -> tuple[str, bool]:
    """
    Generate a tailored cover letter via structured JSON + Pydantic validation.

    Returns:
        (cover_letter_text, True)  — LLM call and validation succeeded
        (fallback_text, False)     — any error occurred; fallback was used
    """
    user_prompt = build_cover_letter_prompt(
        resume_text=resume_text,
        jd_text=jd_text,
        matched_skills=matched_skills,
        missing_skills=missing_skills,
    )

    try:
        raw_json = generate_json(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            temperature=0.4,
        )
        validated = CoverLetterResponse.model_validate(raw_json)
        return validated.cover_letter, True
    except ValidationError:
        # LLM returned JSON that doesn't match our schema
        pass
    except LLMServiceError:
        # OpenAI API failure or unparseable JSON from model
        pass
    except Exception:
        # Catch-all for any unexpected errors
        pass

    return generate_fallback_cover_letter(matched_skills, missing_skills), False
