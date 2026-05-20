"""
API route definitions.

Analyze flow:
1. matcher.match_resume_to_jd() — rule-based score & skills (no LLM)
2. bullet_rewriter.rewrite_resume_bullets() — ONE LLM call for bullets only
3. report_generator.generate_report() — markdown report from match + bullets
"""

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from app.api.schemas import AnalyzeRequest, AnalyzeResponse, ResumeParseResponse
from app.services.resume_parser import ResumeParseError, parse_resume_file
from app.config import OPENAI_API_KEY
from app.services.bullet_rewriter import rewrite_resume_bullets
from app.services.matcher import match_resume_to_jd
from app.services.report_generator import generate_report

root_router = APIRouter(tags=["root"])
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


@api_router.post("/resume/parse", response_model=ResumeParseResponse)
async def parse_resume(file: UploadFile = File(...)) -> ResumeParseResponse:
    """
    Accept a PDF or DOCX resume, extract text, return JSON for the frontend.

    Uses multipart/form-data with field name 'file'.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided.")

    content = await file.read()

    try:
        resume_text = parse_resume_file(file.filename, content)
    except ResumeParseError as exc:
        raise HTTPException(status_code=400, detail=exc.message) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse resume: {exc}",
        ) from exc

    return ResumeParseResponse(resume_text=resume_text)


@api_router.post("/analyze", response_model=AnalyzeResponse)
def analyze_job_match(body: AnalyzeRequest) -> AnalyzeResponse:
    """
    Analyze resume vs job description.

    Scoring is rule-based; only bullet rewriting uses the LLM.
    """
    if not OPENAI_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="OPENAI_API_KEY is not configured. Add it to backend/.env.",
        )

    # Step 1: deterministic matching (no tokens)
    match_result = match_resume_to_jd(body.resume_text, body.jd_text)

    # Step 2: single LLM call for rewritten bullets
    bullets = rewrite_resume_bullets(
        resume_text=body.resume_text,
        jd_text=body.jd_text,
        matched_skills=match_result["matched_skills"],
        missing_skills=match_result["missing_skills"],
    )

    # Step 3: report uses match data + AI bullets (no extra LLM call)
    report = generate_report(match_result, bullets)

    return AnalyzeResponse(
        match_score=match_result["match_score"],
        matched_skills=match_result["matched_skills"],
        missing_skills=match_result["missing_skills"],
        rewritten_bullets=bullets,
        final_report=report,
    )
