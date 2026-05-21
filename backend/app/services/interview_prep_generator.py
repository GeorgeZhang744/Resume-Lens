"""
AI-powered interview prep generation (single structured LLM call per analyze).

Returns a prep dict plus a success flag for LangGraph state tracking.
"""

from pydantic import ValidationError

from app.api.schemas import InterviewPrepResponse
from app.prompts.interview_prep_prompt import (
    SYSTEM_PROMPT,
    build_interview_prep_prompt,
)
from app.services.llm_service import LLMServiceError, generate_json


def generate_fallback_interview_prep(
    matched_skills: list[str],
    missing_skills: list[str],
) -> dict:
    """
    Template interview prep when the LLM or validation fails.

    Uses real matched/missing skills so answers are grounded in the actual resume/JD.
    """
    matched_str = matched_skills[0] if matched_skills else "your primary skill"
    matched_pair = (
        f"{matched_skills[0]} and {matched_skills[1]}"
        if len(matched_skills) >= 2
        else matched_str
    )

    technical_questions = [
        f"Walk me through a project where you used {matched_str} to solve a real problem.",
        f"How do you approach debugging and testing in {matched_str}?",
        f"Describe the architecture of a system you built using {matched_pair}.",
    ]

    behavioral_questions = [
        "Tell me about a time you had to learn a new technology quickly under a deadline.",
        "Describe a situation where you disagreed with a team decision and how you handled it.",
        "Give an example of how you have improved a process or workflow on a past project.",
    ]

    # Study topics are based on the skill gaps identified by the rule-based matcher
    if missing_skills:
        study_topics = [
            f"Core concepts and best practices in {skill}"
            for skill in missing_skills[:5]
        ]
    else:
        study_topics = [
            "Review system design fundamentals (scalability, reliability, databases).",
            "Practice data structures and algorithm problems relevant to the role.",
            "Read the company's engineering blog or public technical documentation.",
        ]

    return {
        "technical_questions": technical_questions,
        "behavioral_questions": behavioral_questions,
        "study_topics": study_topics,
    }


def generate_interview_prep(
    resume_text: str,
    jd_text: str,
    matched_skills: list[str],
    missing_skills: list[str],
) -> tuple[dict, bool]:
    """
    Generate targeted interview prep via structured JSON + Pydantic validation.

    Returns:
        (prep_dict, True)      — LLM call and validation succeeded
        (fallback_dict, False) — any error occurred; fallback was used

    prep_dict keys: technical_questions, behavioral_questions, study_topics
    """
    user_prompt = build_interview_prep_prompt(
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
        validated = InterviewPrepResponse.model_validate(raw_json)
        return {
            "technical_questions": validated.technical_questions,
            "behavioral_questions": validated.behavioral_questions,
            "study_topics": validated.study_topics,
        }, True
    except ValidationError:
        # LLM returned JSON that doesn't match our schema
        pass
    except LLMServiceError:
        # OpenAI API failure or unparseable JSON from model
        pass
    except Exception:
        # Catch-all for any unexpected errors
        pass

    return generate_fallback_interview_prep(matched_skills, missing_skills), False
