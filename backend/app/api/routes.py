"""
API route definitions.

The analyze endpoint now invokes a tool-calling agent (app/agents/graph.py)
rather than a fixed LangGraph pipeline. The agent returns a message history;
this module extracts the structured tool results from that history and maps
them to the AnalyzeResponse schema.
"""

import json
import uuid

from fastapi import APIRouter, File, HTTPException, UploadFile
from langchain_core.messages import AIMessage, ToolMessage

from app.agents.graph import analyze_graph
from app.api.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    ChatRequest,
    ChatResponse,
    HealthResponse,
    ResumeParseResponse,
    RootResponse,
)
from app.config import OPENAI_API_KEY
from app.services.resume_parser import ResumeParseError, parse_resume_file

root_router = APIRouter(tags=["root"])
api_router = APIRouter(tags=["api"])


# ---------------------------------------------------------------------------
# Result extraction helpers
# ---------------------------------------------------------------------------

def _extract_tool_results(messages: list) -> dict:
    """
    Parse every ToolMessage in the agent's message history into a dict keyed
    by tool name.

    Strategy:
      1. Build a tool_call_id → tool_name map from AIMessages (which carry
         the tool_calls metadata).
      2. Match each ToolMessage to a name via that map (or the ToolMessage.name
         attribute when it is set, for forward compatibility).

    If a tool was called more than once, the last result wins — which is always
    the most up-to-date value.
    """
    # Step 1: map call IDs to tool names
    call_id_to_name: dict[str, str] = {}
    for msg in messages:
        if isinstance(msg, AIMessage) and getattr(msg, "tool_calls", None):
            for tc in msg.tool_calls:
                call_id_to_name[tc["id"]] = tc["name"]

    # Step 2: collect and parse ToolMessage content
    results: dict[str, dict] = {}
    for msg in messages:
        if not isinstance(msg, ToolMessage):
            continue
        # Prefer the explicit name attribute; fall back to the ID map
        name = getattr(msg, "name", None) or call_id_to_name.get(
            getattr(msg, "tool_call_id", ""), ""
        )
        if not name:
            continue
        try:
            results[name] = json.loads(msg.content)
        except (json.JSONDecodeError, TypeError):
            results[name] = {}

    return results


def _get_agent_summary(messages: list) -> str:
    """
    Return the final AI message that contains the agent's natural-language
    summary (i.e. the last AIMessage with no pending tool_calls).

    This replaces the old deterministic markdown report — the agent writes
    a personalised analysis based on what its tools returned.
    """
    for msg in reversed(messages):
        if (
            isinstance(msg, AIMessage)
            and msg.content
            and not getattr(msg, "tool_calls", None)
        ):
            return str(msg.content)
    return ""


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

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
    Invoke the tool-calling agent and return structured analysis results.

    The agent receives a single goal message, calls its tools autonomously,
    and produces a message history. This handler extracts the tool outputs
    from that history and maps them to AnalyzeResponse.
    """
    if not OPENAI_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="OPENAI_API_KEY is not configured. Add it to backend/.env.",
        )

    # Single natural-language goal — the agent decides how to handle it
    goal_message = (
        "Analyze this job application.\n\n"
        f"Resume:\n{body.resume_text}\n\n"
        f"Job Description:\n{body.jd_text}"
    )

    # Each analysis gets its own thread so runs are independent but all persisted.
    # The thread_id is a UUID generated per request — no two analyses share state.
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    # Invoke the agent — returns {"messages": [HumanMessage, AIMessage, ToolMessage, ...]}
    final_state = analyze_graph.invoke({"messages": [("human", goal_message)]}, config=config)

    messages = final_state["messages"]

    # Extract structured results from tool call history
    tool_results = _extract_tool_results(messages)
    agent_summary = _get_agent_summary(messages)

    # Pull each tool's output with safe defaults if a tool was skipped or failed
    match_data  = tool_results.get("analyze_resume_match", {})
    bullet_data = tool_results.get("rewrite_resume_bullets_tool", {})
    cl_data     = tool_results.get("write_cover_letter_tool", {})
    ip_data     = tool_results.get("prepare_interview_questions_tool", {})

    return AnalyzeResponse(
        thread_id          = thread_id,
        match_score        = match_data.get("match_score", 0),
        matched_skills     = match_data.get("matched_skills", []),
        missing_skills     = match_data.get("missing_skills", []),
        rewritten_bullets  = bullet_data.get("bullets", []),
        critique_score     = bullet_data.get("quality_score", 0),
        cover_letter       = cl_data.get("cover_letter", ""),
        technical_questions  = ip_data.get("technical_questions", []),
        behavioral_questions = ip_data.get("behavioral_questions", []),
        study_topics         = ip_data.get("study_topics", []),
        final_report = agent_summary,
    )


@api_router.post("/chat", response_model=ChatResponse)
def chat(body: ChatRequest) -> ChatResponse:
    """
    Send a follow-up message to an existing analysis thread.

    The agent already has the full context from the original analysis
    (resume, JD, tool results) stored in the SQLite checkpoint. It picks
    up the thread and responds without needing any of that repeated.

    Example follow-ups:
      "Make the cover letter more formal."
      "Add more detail about my Python experience in the bullets."
      "What should I study first given my skill gaps?"
    """
    if not OPENAI_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="OPENAI_API_KEY is not configured. Add it to backend/.env.",
        )

    config = {"configurable": {"thread_id": body.thread_id}}

    final_state = analyze_graph.invoke(
        {"messages": [("human", body.message)]},
        config=config,
    )

    reply = _get_agent_summary(final_state["messages"])
    return ChatResponse(reply=reply or "I'm not sure how to help with that.")
