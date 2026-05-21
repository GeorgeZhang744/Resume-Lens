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
    """Body for POST /api/analyze."""

    resume_text: str
    jd_text: str


class AnalyzeResponse(BaseModel):
    """JSON returned to the frontend after analysis."""

    match_score: int
    matched_skills: list[str]
    missing_skills: list[str]
    rewritten_bullets: list[str]
    cover_letter: str
    final_report: str


class ResumeParseResponse(BaseModel):
    """JSON returned after POST /api/resume/parse."""

    resume_text: str


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
