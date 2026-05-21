"""
Thin wrapper around the OpenAI Chat Completions API.

- generate_text(): raw assistant string
- generate_json(): parsed dict with retry + safe JSON extraction
"""

import json
import logging
import re
from typing import Any

from openai import APIConnectionError, APIError, APITimeoutError, OpenAI, RateLimitError

from app.config import (
    LLM_JSON_MAX_RETRIES,
    LLM_TIMEOUT_SECONDS,
    OPENAI_API_KEY,
    OPENAI_MODEL,
)

logger = logging.getLogger(__name__)

_client: OpenAI | None = None


class LLMServiceError(Exception):
    """Raised when the LLM call or JSON parsing fails after retries."""


def _get_client() -> OpenAI:
    """Create or return the shared OpenAI client."""
    global _client
    if not OPENAI_API_KEY:
        raise ValueError(
            "OPENAI_API_KEY is not set. Add it to backend/.env and restart the server."
        )
    if _client is None:
        _client = OpenAI(
            api_key=OPENAI_API_KEY,
            timeout=LLM_TIMEOUT_SECONDS,
        )
    return _client


def _strip_json_fences(text: str) -> str:
    """Remove optional ```json ... ``` wrappers from model output."""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```\s*$", "", text)
    return text.strip()


def parse_json_response(text: str) -> dict[str, Any]:
    """
    Parse LLM text into a dict.

    Raises:
        LLMServiceError: If JSON is invalid or not an object.
    """
    cleaned = _strip_json_fences(text)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        logger.warning("JSON parse failed: %s | snippet=%r", exc, cleaned[:200])
        raise LLMServiceError(f"Invalid JSON from LLM: {exc}") from exc

    if not isinstance(data, dict):
        raise LLMServiceError("LLM JSON must be an object at the top level.")

    return data


def generate_text(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.3,
) -> str:
    """
    Send one chat completion request and return assistant text.

    Raises:
        ValueError: Missing API key.
        LLMServiceError: OpenAI API or timeout failure.
    """
    try:
        response = _get_client().chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
        )
        content = response.choices[0].message.content
        if not content or not content.strip():
            raise LLMServiceError("OpenAI returned an empty response.")
        return content.strip()
    except APITimeoutError as exc:
        raise LLMServiceError(f"OpenAI request timed out after {LLM_TIMEOUT_SECONDS}s") from exc
    except (APIError, APIConnectionError, RateLimitError) as exc:
        raise LLMServiceError(f"OpenAI API error: {exc}") from exc


def generate_json(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.3,
) -> dict[str, Any]:
    """
    Call the LLM and return parsed JSON (with at most one retry).

    Raises:
        LLMServiceError: After all attempts fail.
    """
    max_attempts = 1 + LLM_JSON_MAX_RETRIES
    last_error: Exception | None = None

    for attempt in range(1, max_attempts + 1):
        try:
            raw = generate_text(system_prompt, user_prompt, temperature=temperature)
            return parse_json_response(raw)
        except (LLMServiceError, ValueError) as exc:
            last_error = exc
            logger.warning(
                "generate_json attempt %s/%s failed: %s",
                attempt,
                max_attempts,
                exc,
            )

    raise LLMServiceError(str(last_error) if last_error else "Unknown LLM failure")
