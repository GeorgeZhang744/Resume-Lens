"""
API route definitions.

Analyze flow is orchestrated by LangGraph (app/agents/graph.py).
Resume parsing still uses the resume_parser service directly.
"""

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.agents.graph import analyze_graph
from app.api.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    HealthResponse,
    ResumeParseResponse,
    RootResponse,
)
from app.config import OPENAI_API_KEY
from app.services.resume_parser import ResumeParseError, parse_resume_file

root_router = APIRouter(tags=["root"])
api_router = APIRouter(tags=["api"])


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
    Run the LangGraph analyze workflow and return the final state as JSON.
    """
    if not OPENAI_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="OPENAI_API_KEY is not configured. Add it to backend/.env.",
        )

    # Initial state — nodes fill match_result, rewritten_bullets, final_report
    initial_state = {
        "resume_text": body.resume_text,
        "jd_text": body.jd_text,
    }

    final_state = analyze_graph.invoke(initial_state)

    match_result = final_state["match_result"]

    return AnalyzeResponse(
        match_score=match_result["match_score"],
        matched_skills=match_result["matched_skills"],
        missing_skills=match_result["missing_skills"],
        rewritten_bullets=final_state["rewritten_bullets"],
        final_report=final_state["final_report"],
    )
