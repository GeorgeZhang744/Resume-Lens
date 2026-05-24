"""
Application configuration loaded from environment variables.

Loads backend/.env via python-dotenv when this module is imported.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# backend/ directory (parent of app/)
BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")

# OpenAI
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

# Prompt size guard — keeps a single LLM call cheap
MAX_RESUME_CHARS: int = int(os.getenv("MAX_RESUME_CHARS", "4000"))
MAX_JD_CHARS: int = int(os.getenv("MAX_JD_CHARS", "4000"))

# OpenAI request timeout (seconds) and JSON retry attempts (1 retry = 2 total tries)
LLM_TIMEOUT_SECONDS: float = float(os.getenv("LLM_TIMEOUT_SECONDS", "60"))
LLM_JSON_MAX_RETRIES: int = int(os.getenv("LLM_JSON_MAX_RETRIES", "1"))

# JSearch (RapidAPI) — used for job recommendations
RAPIDAPI_KEY: str = os.getenv("RAPIDAPI_KEY", "")
