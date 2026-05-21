"""
Prompts for AI interview prep generation.

The model must return pure JSON matching InterviewPrepResponse in schemas.py.
"""

from app.config import MAX_JD_CHARS, MAX_RESUME_CHARS

SYSTEM_PROMPT = """You are an expert technical recruiter and interview coach.

Generate targeted interview preparation material for a specific job application.

Content rules:
- Technical questions: role-specific, grounded in the job description and matched skills
- Behavioral questions: relevant to the responsibilities and team context in the JD
- Study topics: focused on the candidate's skill gaps (missing skills); practical and actionable
- Keep all questions practical — avoid purely generic questions like "Tell me about yourself"
- Do NOT invent candidate experience or assume facts not in the resume
- Each list must contain exactly 3 to 5 items
- Each item must be a complete, clear sentence or phrase

OUTPUT RULES (critical):
- Return ONLY valid JSON — no markdown, no code fences, no explanations
- Do not include any text before or after the JSON object
- Use exactly this schema:

{
  "technical_questions": ["question 1", "question 2", "question 3"],
  "behavioral_questions": ["question 1", "question 2", "question 3"],
  "study_topics": ["topic 1", "topic 2", "topic 3"]
}"""


def _truncate(text: str, max_chars: int) -> str:
    """Limit prompt size to control token cost."""
    text = text.strip()
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n...[truncated]"


def build_interview_prep_prompt(
    resume_text: str,
    jd_text: str,
    matched_skills: list[str],
    missing_skills: list[str],
) -> str:
    """Build the user message for structured JSON interview prep generation."""
    resume = _truncate(resume_text, MAX_RESUME_CHARS)
    jd = _truncate(jd_text, MAX_JD_CHARS)

    matched = ", ".join(matched_skills) if matched_skills else "None detected"
    missing = ", ".join(missing_skills) if missing_skills else "None"

    return f"""Generate interview preparation material for this job application.

Resume (do not invent beyond this):
{resume}

Job description:
{jd}

Skills the candidate already has (basis for technical questions): {matched}
Skills missing from the resume (basis for study topics): {missing}

Respond with ONLY a JSON object in this exact shape (3–5 items per list):
{{
  "technical_questions": ["...", "...", "..."],
  "behavioral_questions": ["...", "...", "..."],
  "study_topics": ["...", "...", "..."]
}}"""
