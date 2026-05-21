"""
Prompts for AI cover letter generation.

The model must return pure JSON matching CoverLetterResponse in schemas.py.
"""

from app.config import MAX_JD_CHARS, MAX_RESUME_CHARS

SYSTEM_PROMPT = """You are a professional career coach and expert cover letter writer.

Write a tailored cover letter for a specific job application.

Content rules:
- Professional, confident, and enthusiastic tone
- 3 to 5 short paragraphs (opening, skills alignment, value proposition, closing)
- Tailored to the target job description — reference the role and company context if available
- Naturally weave in matched skills; do not keyword-stuff
- If the candidate is missing key skills, acknowledge eagerness to learn — do NOT invent experience
- NEVER invent employers, titles, dates, metrics, or tools not on the resume
- ATS-friendly language — use keywords from the job description naturally
- Do NOT include a salutation line — start directly with the opening paragraph
- Keep the total letter under 400 words

OUTPUT RULES (critical):
- Return ONLY valid JSON — no markdown, no code fences, no explanations
- Do not include any text before or after the JSON object
- Use exactly this schema:

{"cover_letter": "full cover letter text here"}"""


def _truncate(text: str, max_chars: int) -> str:
    """Limit prompt size to control token cost."""
    text = text.strip()
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n...[truncated]"


def build_cover_letter_prompt(
    resume_text: str,
    jd_text: str,
    matched_skills: list[str],
    missing_skills: list[str],
) -> str:
    """Build the user message for structured JSON cover letter generation."""
    resume = _truncate(resume_text, MAX_RESUME_CHARS)
    jd = _truncate(jd_text, MAX_JD_CHARS)

    matched = ", ".join(matched_skills) if matched_skills else "None detected"
    missing = ", ".join(missing_skills) if missing_skills else "None"

    return f"""Write a tailored cover letter for this job application.

Resume (source facts — do not invent beyond this):
{resume}

Job description:
{jd}

Skills already matched (weave in naturally): {matched}
Skills in JD but weak/absent on resume (acknowledge eagerness to learn if relevant): {missing}

Respond with ONLY a JSON object in this exact shape:
{{"cover_letter": "..."}}"""
