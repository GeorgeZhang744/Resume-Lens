"""
Prompts for AI resume bullet rewriting.

The model must return pure JSON matching BulletRewriteResponse in schemas.py.
"""

from app.config import MAX_JD_CHARS, MAX_RESUME_CHARS

SYSTEM_PROMPT = """You are an expert resume writer and ATS optimization coach.

Rewrite resume bullets for a specific job description.

Content rules:
- Use strong action verbs (Led, Built, Delivered, Improved, etc.)
- Align wording with the target job description and ATS keywords
- Emphasize matched skills naturally; do not keyword-stuff
- NEVER invent employers, titles, dates, metrics, or tools not supported by the resume
- If the resume lacks detail, write conservative bullets that could apply without lying
- Each bullet: one concise line; add numbers only if implied by the resume
- Provide 3 to 5 bullets inside the JSON array

OUTPUT RULES (critical):
- Return ONLY valid JSON — no markdown, no code fences, no explanations
- Do not include any text before or after the JSON object
- Use exactly this schema:

{"rewritten_bullets": ["bullet text 1", "bullet text 2", "bullet text 3"]}"""


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
    critique_feedback: list[str] | None = None,
) -> str:
    """
    Build the user message for structured JSON bullet rewriting.

    If critique_feedback is provided, this is a retry attempt — the specific
    issues from the previous critique are injected so the LLM fixes them.
    """
    resume = _truncate(resume_text, MAX_RESUME_CHARS)
    jd = _truncate(jd_text, MAX_JD_CHARS)

    matched = ", ".join(matched_skills) if matched_skills else "None detected"
    missing = ", ".join(missing_skills) if missing_skills else "None"

    # On retry: prepend the critique issues so the LLM knows exactly what to fix
    feedback_section = ""
    if critique_feedback:
        issues = "\n".join(f"- {issue}" for issue in critique_feedback)
        feedback_section = f"""IMPORTANT — This is a retry. A previous attempt was reviewed and rejected.
Fix ALL of these specific issues in your new attempt:
{issues}

"""

    return f"""Rewrite resume bullets for this job application.

{feedback_section}Resume (source facts — do not invent beyond this):
{resume}

Job description:
{jd}

Skills already matched (weave in naturally): {matched}
Skills in JD but weak/absent on resume: {missing}

Respond with ONLY a JSON object in this exact shape (3–5 bullets in the array):
{{"rewritten_bullets": ["...", "...", "..."]}}"""
