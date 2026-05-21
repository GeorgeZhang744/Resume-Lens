"""
Bullet quality critique service.

Calls the LLM to evaluate rewritten bullets against the JD and returns:
  - verdict: "accept" or "retry"
  - score:   1–10 (0 means the critique call itself failed)
  - issues:  specific actionable problems (empty on accept)

A failing critique ALWAYS defaults to "accept" so it never blocks the pipeline.
Used by critique_node in nodes.py to drive the self-critique loop.
"""

from pydantic import ValidationError

from app.api.schemas import CritiqueResponse
from app.prompts.critique_prompt import SYSTEM_PROMPT, build_critique_prompt
from app.services.llm_service import LLMServiceError, generate_json


def _fallback_critique() -> dict:
    """
    Safe default when the critique LLM call fails for any reason.

    Returns "accept" with score=0 so the pipeline always continues.
    A score of 0 is distinguishable from a real score and signals the
    critique itself failed — not that the bullets are good.
    """
    return {"verdict": "accept", "score": 0, "issues": []}


def critique_bullets(
    bullets: list[str],
    jd_text: str,
    resume_text: str,
    matched_skills: list[str],
) -> tuple[dict, bool]:
    """
    Evaluate bullet quality via structured LLM critique + Pydantic validation.

    Args:
        bullets:        The rewritten bullets to evaluate.
        jd_text:        The job description (for ATS alignment check).
        resume_text:    The original resume (for fact-checking only).
        matched_skills: Skills the candidate already has (should appear in bullets).

    Returns:
        (critique_dict, True)  — LLM call and validation succeeded
        (fallback_dict, False) — any error; always defaults to "accept"

    critique_dict keys:
        verdict (str):   "accept" or "retry"
        score   (int):   1–10 quality score (0 = critique failed)
        issues  (list):  specific problems found; empty on accept
    """
    # Nothing to evaluate — skip the LLM call entirely
    if not bullets:
        return _fallback_critique(), False

    user_prompt = build_critique_prompt(
        bullets=bullets,
        jd_text=jd_text,
        resume_text=resume_text,
        matched_skills=matched_skills,
    )

    try:
        raw_json = generate_json(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            temperature=0.1,  # Low temperature — we want consistent, reproducible scoring
        )
        validated = CritiqueResponse.model_validate(raw_json)
        return {
            "verdict": validated.verdict,
            "score": validated.score,
            "issues": validated.issues,
        }, True
    except ValidationError:
        # LLM returned JSON that doesn't match our schema
        pass
    except LLMServiceError:
        # OpenAI API failure or unparseable JSON
        pass
    except Exception:
        # Catch-all — critique must never crash the pipeline
        pass

    return _fallback_critique(), False
