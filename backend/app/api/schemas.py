"""
Pydantic models for API request/response bodies.
Keeps route handlers thin and documents the JSON contract.
"""

from pydantic import BaseModel, Field, field_validator


class RootResponse(BaseModel):
    """Response body for GET /."""

    message: str


class HealthResponse(BaseModel):
    """Response body for GET /health."""

    status: str


class AnalyzeRequest(BaseModel):
    """Body for POST /api/analyze.

    services controls which optional tools the agent runs. The skill match
    analysis always runs regardless. Valid values:
      "rewrite_bullets" — rewrite resume bullets with self-critique
      "cover_letter"    — generate a tailored cover letter
      "interview_prep"  — generate questions and study topics
    Defaults to all three when omitted.
    """

    resume_text: str
    jd_text: str
    sections: list[str] = ["rewrite_bullets", "cover_letter", "interview_prep"]


class AnalyzeResponse(BaseModel):
    """JSON returned to the frontend after analysis."""

    thread_id: str
    match_score: int
    matched_skills: list[str]
    missing_skills: list[str]
    rewritten_bullets: list[str]
    critique_score: int
    cover_letter: str
    technical_questions: list[str]
    behavioral_questions: list[str]
    study_topics: list[str]
    final_report: str


class ChatRequest(BaseModel):
    """Body for POST /api/chat."""

    thread_id: str
    message: str


class ChatResponse(BaseModel):
    """JSON returned from POST /api/chat.

    updates is a partial AnalyzeResponse — only the fields that the agent
    actually rewrote this turn are present. Empty dict means the agent just
    answered a question without calling any tools.
    """

    reply: str
    updates: dict = {}


class ResumeParseResponse(BaseModel):
    """JSON returned after POST /api/resume/parse."""

    resume_text: str


class CritiqueResponse(BaseModel):
    """Validated shape of the LLM JSON response for bullet critique."""

    verdict: str
    score: int = Field(..., ge=1, le=10, description="Quality score 1–10")
    issues: list[str] = Field(default_factory=list)

    @field_validator("verdict")
    @classmethod
    def verdict_must_be_valid(cls, v: str) -> str:
        v = v.strip().lower()
        if v not in ("accept", "retry"):
            raise ValueError("verdict must be 'accept' or 'retry'")
        return v

    @field_validator("issues")
    @classmethod
    def strip_empty_issues(cls, items: list[str]) -> list[str]:
        return [item.strip() for item in items if item.strip()]


class InterviewPrepResponse(BaseModel):
    """Validated shape of the LLM JSON response for interview prep generation."""

    technical_questions: list[str] = Field(
        ..., min_length=3, max_length=5, description="3–5 technical interview questions"
    )
    behavioral_questions: list[str] = Field(
        ..., min_length=3, max_length=5, description="3–5 behavioral interview questions"
    )
    study_topics: list[str] = Field(
        ..., min_length=3, max_length=5, description="3–5 study topics based on skill gaps"
    )

    @field_validator("technical_questions", "behavioral_questions", "study_topics")
    @classmethod
    def items_must_be_non_empty(cls, items: list[str]) -> list[str]:
        cleaned = [item.strip() for item in items]
        if any(not item for item in cleaned):
            raise ValueError("Each item must be a non-empty string.")
        return cleaned


class CoverLetterResponse(BaseModel):
    """Validated shape of the LLM JSON response for cover letter generation."""

    cover_letter: str

    @field_validator("cover_letter")
    @classmethod
    def cover_letter_must_be_non_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("cover_letter must be a non-empty string.")
        return v


class JobSearchRequest(BaseModel):
    """Body for POST /api/jobs."""

    resume_text: str


class JobResult(BaseModel):
    """A single job listing returned by the job search."""

    job_id: str
    title: str
    company: str
    location: str
    employment_type: str
    apply_link: str
    description: str
    salary: str


class JobSearchResponse(BaseModel):
    """Response for POST /api/jobs."""

    jobs: list[JobResult]


class BulletRewriteResponse(BaseModel):
    """Validated shape of the LLM JSON response for bullet rewriting."""

    rewritten_bullets: list[str] = Field(
        ...,
        min_length=1,
        max_length=5,
        description="Between 1 and 5 resume bullets",
    )

    @field_validator("rewritten_bullets")
    @classmethod
    def bullets_must_be_non_empty(cls, bullets: list[str]) -> list[str]:
        cleaned = [b.strip() for b in bullets]
        if any(not b for b in cleaned):
            raise ValueError("Each bullet must be a non-empty string.")
        return cleaned
