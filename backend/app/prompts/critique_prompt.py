"""
Prompts for AI bullet quality critique.

The model evaluates rewritten resume bullets and returns a structured verdict:
  "accept" — bullets are strong enough to proceed
  "retry"  — bullets have specific fixable problems

Used by bullet_critic.py to drive the self-critique loop in LangGraph.
"""

from app.config import MAX_JD_CHARS, MAX_RESUME_CHARS

SYSTEM_PROMPT = """You are a strict ATS optimization specialist and resume coach.

Your job is to evaluate a set of rewritten resume bullets against a job description.

Score the bullets on 5 criteria (each worth 2 points, total out of 10):

1. ATS keyword alignment  — do bullets use exact keywords and phrases from the JD?
2. Action verb strength   — do bullets open with strong verbs (Built, Led, Delivered, Reduced)?
3. Factual integrity      — do bullets stay within what the resume supports? No invented metrics/tools.
4. Specificity            — are bullets concrete rather than vague and generic?
5. Role relevance         — do bullets address what the JD is actually looking for?

Verdict rules (apply strictly):
- score >= 7 → verdict = "accept"
- score <  7 → verdict = "retry"

When verdict is "retry", the issues list MUST contain specific, actionable problems.
When verdict is "accept", issues may be empty or contain minor notes.

OUTPUT RULES (critical):
- Return ONLY valid JSON — no markdown, no code fences, no explanations
- Use exactly this schema:

{"verdict": "accept", "score": 8, "issues": ["issue 1", "issue 2"]}"""


def _truncate(text: str, max_chars: int) -> str:
    """Limit prompt size to control token cost."""
    text = text.strip()
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n...[truncated]"


def build_critique_prompt(
    bullets: list[str],
    jd_text: str,
    resume_text: str,
    matched_skills: list[str],
) -> str:
    """Build the user message for structured JSON bullet critique."""
    jd = _truncate(jd_text, MAX_JD_CHARS)
    # Use half the resume limit — critique only needs it for fact-checking
    resume = _truncate(resume_text, MAX_RESUME_CHARS // 2)
    bullet_lines = "\n".join(f"{i + 1}. {b}" for i, b in enumerate(bullets))
    matched = ", ".join(matched_skills) if matched_skills else "None"

    return f"""Evaluate these rewritten resume bullets for quality and ATS alignment.

Job description:
{jd}

Original resume (for fact-checking only — bullets must not invent beyond this):
{resume}

Skills that should appear naturally in the bullets: {matched}

Rewritten bullets to evaluate:
{bullet_lines}

Score 1–10 and return your verdict as JSON.
Reminder: score >= 7 → "accept", score < 7 → "retry" with specific issues."""
