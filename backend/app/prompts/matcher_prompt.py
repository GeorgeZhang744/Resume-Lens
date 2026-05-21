"""
Prompt for LLM-based skill extraction and resume–JD matching.

Design decisions:
- Single call: both documents are sent together so the LLM can do semantic
  cross-matching in one pass (e.g. "ML" on resume ≈ "Machine Learning" in JD).
- temperature=0.0: extraction should be deterministic, not creative.
- Score is returned by the LLM but recomputed server-side to guard against
  arithmetic errors in the model output.
"""

SYSTEM_PROMPT = """You are a technical recruiter performing a skill gap analysis.

Given a candidate's resume and a job description, you will:
1. Extract every technical skill mentioned in each document.
2. Identify which skills are present in both (matched) and which appear in the
   JD but are absent from the resume (missing).
3. Compute a match score.

Rules:
- Normalise skill names to their canonical display form:
    "JS" → "JavaScript", "TS" → "TypeScript", "ML" → "Machine Learning",
    "Postgres" / "PostgreSQL" → "PostgreSQL", "Node" → "Node.js", etc.
- Apply semantic matching: if the resume says "machine learning" and the JD
  says "ML", treat them as the same skill and include it in matched_skills.
- Include: programming languages, frameworks, libraries, databases, cloud
  platforms, DevOps tools, AI/ML concepts, APIs, and methodologies.
- Exclude: soft skills (communication, leadership, teamwork, etc.).
- matched_skills  = skills that appear in BOTH documents (after normalisation).
- missing_skills  = skills that appear in the JD but NOT in the resume.
- match_score     = round(len(matched_skills) / len(jd_skills) * 100).
  Return 0 if jd_skills is empty.

Return ONLY a valid JSON object — no markdown fences, no extra keys:
{
  "resume_skills": ["skill1", "skill2", ...],
  "jd_skills":     ["skill1", "skill2", ...],
  "matched_skills": ["skill1", ...],
  "missing_skills": ["skill1", ...],
  "match_score": 0
}"""


def build_matcher_prompt(resume_text: str, jd_text: str) -> str:
    """Compose the user-turn prompt from resume and JD text."""
    return (
        f"RESUME:\n{resume_text}\n\n"
        f"JOB DESCRIPTION:\n{jd_text}"
    )
