"""
Job search service using the JSearch API (via RapidAPI).

Extracts a concise search query from the resume text via a single LLM call,
then fires one JSearch request. Returns up to 8 slim job dicts.

Returns [] gracefully when:
  - RAPIDAPI_KEY is not set
  - resume_text is empty
  - the LLM or API call fails for any reason
"""

import json
import urllib.parse
import urllib.request

from openai import OpenAI

from app.config import OPENAI_API_KEY, OPENAI_MODEL, RAPIDAPI_KEY

_JSEARCH_URL = "https://jsearch.p.rapidapi.com/search"
_TIMEOUT = 15  # seconds


def search_jobs(resume_text: str) -> list[dict]:
    """
    Search for jobs based on the user's resume.
    Returns up to 8 slim job dicts.
    """
    if not RAPIDAPI_KEY or not resume_text.strip():
        return []

    query = _extract_search_query(resume_text)
    if not query:
        return []

    params = urllib.parse.urlencode(
        {"query": query, "num_pages": "1", "page": "1", "date_posted": "all"}
    )
    url = f"{_JSEARCH_URL}?{params}"

    req = urllib.request.Request(
        url,
        headers={
            "X-RapidAPI-Key": RAPIDAPI_KEY,
            "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            data = json.loads(resp.read().decode())
    except Exception:
        return []

    jobs = data.get("data", [])

    return [
        {
            "job_id": j.get("job_id", ""),
            "title": j.get("job_title", ""),
            "company": j.get("employer_name", ""),
            "location": _format_location(j),
            "employment_type": _format_employment_type(j.get("job_employment_type", "")),
            "apply_link": j.get("job_apply_link", ""),
            "description": (j.get("job_description", "") or "")[:400],
            "salary": _format_salary(j),
        }
        for j in jobs[:8]
    ]


def _extract_search_query(resume_text: str) -> str:
    """
    Use the LLM to derive a short, effective job search query from the resume.
    Returns a string like 'Software Engineer Python React' or '' on failure.
    """
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            temperature=0.0,
            max_tokens=20,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Extract a short job search query (3–5 words) from this resume. "
                        "Format: job title + 1-2 key skills. Example: 'Software Engineer Python React'. "
                        "Return ONLY the query, nothing else."
                    ),
                },
                {"role": "user", "content": resume_text[:2000]},
            ],
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return ""


def _format_location(j: dict) -> str:
    parts = [j.get("job_city", ""), j.get("job_state", ""), j.get("job_country", "")]
    return ", ".join(p for p in parts if p)


def _format_employment_type(raw: str) -> str:
    return raw.replace("_", " ").title() if raw else ""


def _format_salary(j: dict) -> str:
    min_sal = j.get("job_min_salary")
    max_sal = j.get("job_max_salary")
    period = (j.get("job_salary_period") or "").lower()
    if min_sal and max_sal:
        return f"${int(min_sal):,} – ${int(max_sal):,} / {period}" if period else f"${int(min_sal):,} – ${int(max_sal):,}"
    if min_sal:
        return f"${int(min_sal):,}+ / {period}" if period else f"${int(min_sal):,}+"
    return ""
