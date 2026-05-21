"""
Pydantic models for API request/response bodies.
Keeps route handlers thin and documents the JSON contract.
"""

from pydantic import BaseModel


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
    final_report: str


class ResumeParseResponse(BaseModel):
    """JSON returned after POST /api/resume/parse."""

    resume_text: str
