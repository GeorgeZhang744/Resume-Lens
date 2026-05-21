"""
LangChain tool definitions for the job application agent.

Each tool wraps an existing service. The LLM calls these tools autonomously —
it decides which tools to invoke, in what order, and with what arguments.

Design rules:
- Tools accept plain primitive types so the LLM can call them without
  complex object construction.
- All return values are JSON strings so the LLM can read and reason about
  intermediate results before deciding what to call next.
- Errors are caught inside each tool and returned as structured error fields
  rather than raised — the agent handles failures gracefully without crashing.
- The rewrite tool embeds the self-critique loop so bullet quality is always
  gate-checked before the agent moves on.
"""

import json

from langchain_core.tools import tool

from app.services.bullet_critic import critique_bullets
from app.services.bullet_rewriter import generate_fallback_bullets, rewrite_resume_bullets
from app.services.cover_letter_generator import (
    generate_cover_letter,
    generate_fallback_cover_letter,
)
from app.services.interview_prep_generator import (
    generate_fallback_interview_prep,
    generate_interview_prep,
)
from app.services.matcher import match_resume_to_jd


@tool
def analyze_resume_match(resume_text: str, jd_text: str) -> str:
    """Compare resume skills against a job description using rule-based extraction.

    Always call this tool first. The match_score, matched_skills, and
    missing_skills it returns are required inputs for all other tools.

    Returns JSON with:
      match_score     (int)   0-100 alignment percentage
      matched_skills  (list)  skills present on both resume and JD
      missing_skills  (list)  skills in the JD but absent from the resume
      resume_skills   (list)  all skills detected on the resume
      jd_skills       (list)  all skills detected in the JD
    """
    try:
        result = match_resume_to_jd(resume_text=resume_text, jd_text=jd_text)
        return json.dumps(result)
    except Exception as exc:
        return json.dumps({
            "match_score": 0,
            "matched_skills": [],
            "missing_skills": [],
            "resume_skills": [],
            "jd_skills": [],
            "error": str(exc),
        })


@tool
def rewrite_resume_bullets_tool(
    resume_text: str,
    jd_text: str,
    matched_skills: list[str],
    missing_skills: list[str],
) -> str:
    """Rewrite resume bullets for ATS alignment with a built-in self-critique loop.

    After the initial rewrite, an LLM critique scores the bullets (1-10).
    If the score is below 7, the bullets are rewritten once more with the
    specific issues injected into the prompt. The best result is returned.

    Call analyze_resume_match first and pass its matched_skills and
    missing_skills here.

    Returns JSON with:
      bullets         (list)  3-5 rewritten resume bullets
      quality_score   (int)   1-10 final quality score (0 = critique call failed)
      critique_issues (list)  issues found; empty when quality is high
    """
    # --- First rewrite attempt ---
    result = rewrite_resume_bullets(
        resume_text=resume_text,
        jd_text=jd_text,
        matched_skills=matched_skills,
        missing_skills=missing_skills,
    )
    bullets = result["rewritten_bullets"]

    # --- Critique pass ---
    critique, critique_ok = critique_bullets(
        bullets=bullets,
        jd_text=jd_text,
        resume_text=resume_text,
        matched_skills=matched_skills,
    )

    # --- Retry once if critique rejected the bullets ---
    if critique_ok and critique["verdict"] == "retry" and critique["issues"]:
        retry_result = rewrite_resume_bullets(
            resume_text=resume_text,
            jd_text=jd_text,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            critique_feedback=critique["issues"],
        )
        bullets = retry_result["rewritten_bullets"]

        # Score the retry to report the final quality
        final_critique, _ = critique_bullets(
            bullets=bullets,
            jd_text=jd_text,
            resume_text=resume_text,
            matched_skills=matched_skills,
        )
        return json.dumps({
            "bullets": bullets,
            "quality_score": final_critique.get("score", critique["score"]),
            "critique_issues": final_critique.get("issues", []),
        })

    # Bullets were accepted on the first attempt
    return json.dumps({
        "bullets": bullets,
        "quality_score": critique.get("score", 0),
        "critique_issues": critique.get("issues", []),
    })


@tool
def write_cover_letter_tool(
    resume_text: str,
    jd_text: str,
    matched_skills: list[str],
    missing_skills: list[str],
) -> str:
    """Generate a tailored cover letter for the job application.

    Produces a professional 3-5 paragraph letter that weaves in matched skills,
    acknowledges gaps without inventing experience, and uses ATS-friendly language.

    Call analyze_resume_match first and pass its matched_skills and
    missing_skills here.

    Returns JSON with:
      cover_letter  (str)   the full cover letter text
      llm_success   (bool)  False if a fallback template was used instead
    """
    try:
        letter, success = generate_cover_letter(
            resume_text=resume_text,
            jd_text=jd_text,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
        )
        return json.dumps({"cover_letter": letter, "llm_success": success})
    except Exception as exc:
        fallback = generate_fallback_cover_letter(matched_skills, missing_skills)
        return json.dumps({
            "cover_letter": fallback,
            "llm_success": False,
            "error": str(exc),
        })


@tool
def prepare_interview_questions_tool(
    resume_text: str,
    jd_text: str,
    matched_skills: list[str],
    missing_skills: list[str],
) -> str:
    """Generate targeted interview preparation material for the job application.

    Produces role-specific technical questions based on matched skills,
    behavioral questions grounded in the JD context, and practical study
    topics for each skill gap.

    Call analyze_resume_match first and pass its matched_skills and
    missing_skills here.

    Returns JSON with:
      technical_questions  (list)  3-5 technical interview questions
      behavioral_questions (list)  3-5 behavioral interview questions
      study_topics         (list)  3-5 study topics targeting skill gaps
      llm_success          (bool)  False if a fallback was used instead
    """
    try:
        prep, success = generate_interview_prep(
            resume_text=resume_text,
            jd_text=jd_text,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
        )
        return json.dumps({**prep, "llm_success": success})
    except Exception as exc:
        fallback = generate_fallback_interview_prep(matched_skills, missing_skills)
        return json.dumps({**fallback, "llm_success": False, "error": str(exc)})


# All tools exported for create_react_agent
AGENT_TOOLS = [
    analyze_resume_match,
    rewrite_resume_bullets_tool,
    write_cover_letter_tool,
    prepare_interview_questions_tool,
]
