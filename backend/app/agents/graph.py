"""
LangGraph agent definition for resume-JD analysis.

Architecture evolution
──────────────────────
v1 — Fixed pipeline (nodes.py):
     START → match → rewrite → critique → cover_letter → interview_prep → report → END
     The code controlled every step. The LLM was called when told to.

v2 — Tool-calling agent (this file):
     The LLM receives the resume + JD and a set of tools.
     It decides which tools to call, in what order, and with what arguments.
     This is the inversion that makes it a genuine agent.

v3 — Persistent checkpointer (current):
     A SqliteSaver checkpointer is attached so every agent run is persisted to
     checkpoints.db. routes.py passes a unique thread_id per request, keeping
     each analysis independent while making the full message history replayable.

How it works
────────────
1. routes.py sends a single natural-language goal message to the agent.
2. The LLM reads the goal, calls analyze_resume_match to understand the gap,
   then calls the remaining tools using the match results as inputs.
3. After all tools complete, the LLM writes a short personalised summary.
4. routes.py extracts the tool results from the message history and builds
   the structured AnalyzeResponse.

The self-critique loop is preserved — it lives inside rewrite_resume_bullets_tool
so bullet quality is always gate-checked regardless of which path the agent takes.
"""

import sqlite3
from pathlib import Path

from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.prebuilt import create_react_agent

from app.agents.agent_tools import AGENT_TOOLS
from app.config import OPENAI_API_KEY, OPENAI_MODEL

AGENT_SYSTEM_PROMPT = """You are an expert job application copilot.

Given a resume and a job description, help the candidate optimise their application
by using your available tools in a smart sequence.

Available tools:
  analyze_resume_match            — extracts and scores skill alignment (call this first)
  rewrite_resume_bullets_tool     — rewrites bullets with ATS optimisation + self-critique
  write_cover_letter_tool         — generates a tailored cover letter
  prepare_interview_questions_tool — generates questions and skill-gap study topics

Workflow:
1. Always call analyze_resume_match first to understand the skill alignment.
2. Pass matched_skills and missing_skills from the match result into every other tool.
3. Call rewrite_resume_bullets_tool, write_cover_letter_tool, and
   prepare_interview_questions_tool using those values.
4. After all tools have been called, write a concise 2-3 sentence personalised
   summary of the analysis — highlight the match score, key strengths, and the
   most important gap to address.

Decision rules:
- match_score < 20 : note the significant skill gap clearly in your summary.
- match_score 20-69: balanced summary; call out top 2 missing skills.
- match_score >= 70: emphasise the strong alignment; frame gaps as growth areas.

Be decisive. Do not ask clarifying questions — work with what you have been given."""


def _add_system_prompt(state: dict) -> list:
    """Prepend the system prompt to every agent invocation.
    Passed to create_react_agent via the 'prompt' parameter (renamed from
    'state_modifier' in LangGraph 0.3+).
    """
    return [SystemMessage(content=AGENT_SYSTEM_PROMPT)] + list(state["messages"])


# ChatOpenAI is used here because create_react_agent requires a LangChain
# chat model for tool-calling. The existing llm_service.py (plain openai SDK)
# is still used by every tool internally — no duplication of API logic.
_llm = ChatOpenAI(
    model=OPENAI_MODEL,
    api_key=OPENAI_API_KEY,
    temperature=0.3,
)

# SQLite checkpointer ─────────────────────────────────────────────────────────
# Persists the full message history for every agent run to checkpoints.db.
# check_same_thread=False is required because FastAPI may dispatch requests
# from different threads while sharing this single connection object.
# The DB file lives at backend/checkpoints.db (already in .gitignore via *.db).
_DB_PATH = Path(__file__).parent.parent.parent / "checkpoints.db"
_conn = sqlite3.connect(str(_DB_PATH), check_same_thread=False)
_checkpointer = SqliteSaver(_conn)

# The compiled agent — exported as analyze_graph so routes.py requires no
# import changes. The checkpointer is transparent to callers: routes.py just
# needs to pass config={"configurable": {"thread_id": <id>}} on each invoke.
analyze_graph = create_react_agent(
    _llm,
    AGENT_TOOLS,
    prompt=_add_system_prompt,
    checkpointer=_checkpointer,
)
