"""
Prompts for AI resume bullet rewriting.

Prompt text lives here — not in bullet_rewriter.py — so it is easy to tune.
"""

from app.config import MAX_JD_CHARS, MAX_RESUME_CHARS

SYSTEM_PROMPT = """You are an expert resume writer and ATS optimization coach.

Rewrite resume bullets for a specific job description.

Rules:
- Use strong action verbs (Led, Built, Delivered, Improved, etc.)
- Align wording with the target job description and ATS keywords
- Emphasize matched skills naturally; do not keyword-stuff
- NEVER invent employers, titles, dates, metrics, or tools not supported by the resume
- If the resume lacks detail, write conservative bullets that could apply without lying
- Each bullet: one line, concise, impact-oriented; add numbers only if implied by the resume
- Output 3 to 5 bullets maximum

Output format (exactly):
- bullet 1
- bullet 2
- bullet 3

Use that list format only. No intro, no conclusion, no markdown headers."""


def _truncate(text: str, max_chars: int) -> str:
    """Limit prompt size to control token cost."""
    text = text.strip()
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n...[truncated]"


def build_bullet_rewrite_prompt(
    resume_text: str,
    jd_text: str,
    matched_skills: list[str],
    missing_skills: list[str],
) -> str:
    """
    Build the user message sent with SYSTEM_PROMPT to the LLM.

    Includes only what is needed for rewriting (not full scoring logic).
    """
    resume = _truncate(resume_text, MAX_RESUME_CHARS)
    jd = _truncate(jd_text, MAX_JD_CHARS)

    matched = ", ".join(matched_skills) if matched_skills else "None detected"
    missing = ", ".join(missing_skills) if missing_skills else "None"

    return f"""Rewrite resume bullets for this job application.

## Resume (source facts — do not invent beyond this)
{resume}

## Job description
{jd}

## Skills already matched (weave in naturally)
{matched}

## Skills in JD but weak/absent on resume (only suggest if resume has related experience)
{missing}

Return 3–5 bullets using the required list format:
- bullet 1
- bullet 2
- bullet 3"""
