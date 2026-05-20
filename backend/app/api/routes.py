"""
API route definitions.

This module holds FastAPI APIRouter instances. Routers keep endpoints
organized and separate from app setup in main.py.
"""

from fastapi import APIRouter
from pydantic import BaseModel

# Router for public endpoints (root + health checks)
root_router = APIRouter(tags=["root"])

# Router for future REST API endpoints (mounted at /api in main.py)
api_router = APIRouter(tags=["api"])


class RootResponse(BaseModel):
    """Response body for GET /."""

    message: str


class HealthResponse(BaseModel):
    """Response body for GET /health."""

    status: str


@root_router.get("/", response_model=RootResponse)
def read_root() -> RootResponse:
    """Confirm the backend is running."""
    return RootResponse(message="AI Job Match Agent Backend Running")


@root_router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Simple health check for monitoring and load balancers."""
    return HealthResponse(status="ok")


class AnalyzeRequest(BaseModel):
    """Body for POST /api/analyze."""

    resume_text: str
    jd_text: str


class AnalyzeResponse(BaseModel):
    """Mock analyze result until AI logic is added."""

    match_score: int
    matched_skills: list[str]
    missing_skills: list[str]
    rewritten_bullets: list[str]
    final_report: str


@api_router.post("/analyze", response_model=AnalyzeResponse)
def analyze_job_match(body: AnalyzeRequest) -> AnalyzeResponse:
    """Mock job match analysis for frontend MVP."""
    return AnalyzeResponse(
        match_score=80,
        matched_skills=["Python", "FastAPI"],
        missing_skills=["LangGraph"],
        rewritten_bullets=[
            "Built backend APIs using FastAPI to support AI-powered resume analysis."
        ],
        final_report="This is a mock job match report.",
    )
