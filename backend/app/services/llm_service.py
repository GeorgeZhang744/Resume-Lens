"""
Thin wrapper around the OpenAI Chat Completions API.

One function (`generate_text`) is used by higher-level services (e.g. bullet rewriter).
"""

from openai import APIConnectionError, APIError, OpenAI, RateLimitError

from app.config import OPENAI_API_KEY, OPENAI_MODEL

# Reused client instance (created on first call)
_client: OpenAI | None = None


def _get_client() -> OpenAI:
    """Create or return the shared OpenAI client."""
    global _client
    if not OPENAI_API_KEY:
        raise ValueError(
            "OPENAI_API_KEY is not set. Add it to backend/.env and restart the server."
        )
    if _client is None:
        _client = OpenAI(api_key=OPENAI_API_KEY)
    return _client


def generate_text(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.3,
) -> str:
    """
    Send one chat completion request and return assistant text.

    Args:
        system_prompt: Instructions / role for the model.
        user_prompt: User message with resume/JD context.
        temperature: Lower = more deterministic (default 0.3).

    Raises:
        ValueError: Missing API key.
        RuntimeError: OpenAI API failure.
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
            raise RuntimeError("OpenAI returned an empty response.")
        return content.strip()
    except (APIError, APIConnectionError, RateLimitError) as exc:
        raise RuntimeError(f"OpenAI API error: {exc}") from exc
