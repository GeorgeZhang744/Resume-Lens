"""
Rule-based skill extraction and resume–JD matching.

No LLM: we scan text for known skill keywords and compute overlap.
"""

import re
from typing import TypedDict

# Canonical skills we look for in resume and job description text
SKILLS: list[str] = [
    "python",
    "java",
    "c++",
    "javascript",
    "typescript",
    "react",
    "node.js",
    "express.js",
    "sql",
    "postgres",
    "mongodb",
    "docker",
    "rest api",
    "fastapi",
    "machine learning",
    "pytorch",
    "langgraph",
    "openai",
    "llm",
    "rag",
]

# Short forms → canonical skill name (must exist in SKILLS)
ALIASES: dict[str, str] = {
    "js": "javascript",
    "node": "node.js",
    "postgresql": "postgres",
    "ml": "machine learning",
    "llms": "llm",
}

# Pretty labels for API / UI (canonical key → display string)
DISPLAY_NAMES: dict[str, str] = {
    "python": "Python",
    "java": "Java",
    "c++": "C++",
    "javascript": "JavaScript",
    "typescript": "TypeScript",
    "react": "React",
    "node.js": "Node.js",
    "express.js": "Express.js",
    "sql": "SQL",
    "postgres": "PostgreSQL",
    "mongodb": "MongoDB",
    "docker": "Docker",
    "rest api": "REST API",
    "fastapi": "FastAPI",
    "machine learning": "Machine Learning",
    "pytorch": "PyTorch",
    "langgraph": "LangGraph",
    "openai": "OpenAI",
    "llm": "LLM",
    "rag": "RAG",
}


class MatchResult(TypedDict):
    """Structured output from match_resume_to_jd."""

    match_score: int
    matched_skills: list[str]
    missing_skills: list[str]
    resume_skills: list[str]
    jd_skills: list[str]


def normalize_skill(skill: str) -> str:
    """
    Lowercase and map aliases (e.g. 'js' → 'javascript').
    Unknown tokens are returned lowercased as-is.
    """
    cleaned = skill.strip().lower()
    return ALIASES.get(cleaned, cleaned)


def display_skill(skill: str) -> str:
    """Convert canonical skill id to a human-readable label."""
    canonical = normalize_skill(skill)
    return DISPLAY_NAMES.get(canonical, canonical.title())


def extract_skills(text: str) -> list[str]:
    """
    Find skills mentioned in text.

    1. Match longer phrases first (e.g. 'machine learning' before 'learning').
    2. Then check alias tokens with word boundaries to reduce false positives.
    """
    text_lower = text.lower()
    found_set: set[str] = set()
    found_order: list[str] = []

    def add_canonical(canonical: str) -> None:
        if canonical in SKILLS and canonical not in found_set:
            found_set.add(canonical)
            found_order.append(canonical)

    # Pass 1: direct keyword match (longest skills first)
    for skill in sorted(SKILLS, key=len, reverse=True):
        if skill in text_lower:
            add_canonical(skill)

    # Pass 2: alias match (e.g. "js" as a whole token, not inside "projects")
    for alias, canonical in ALIASES.items():
        if canonical in found_set:
            continue
        # Boundaries: alias not glued to other letters/digits (allow dots for node.js-style)
        pattern = rf"(?<![a-z0-9]){re.escape(alias)}(?![a-z0-9])"
        if re.search(pattern, text_lower):
            add_canonical(canonical)

    return found_order


def match_resume_to_jd(resume_text: str, jd_text: str) -> MatchResult:
    """
    Compare resume skills to job-description skills.

    match_score = (matched JD skills / total JD skills) × 100
    """
    resume_skills = extract_skills(resume_text)
    jd_skills = extract_skills(jd_text)

    resume_set = set(resume_skills)

    # Preserve JD order for stable output
    matched_canonical = [s for s in jd_skills if s in resume_set]
    missing_canonical = [s for s in jd_skills if s not in resume_set]

    total_jd = len(jd_skills)
    if total_jd == 0:
        match_score = 0
    else:
        match_score = round(len(matched_canonical) / total_jd * 100)

    return {
        "match_score": match_score,
        "matched_skills": [display_skill(s) for s in matched_canonical],
        "missing_skills": [display_skill(s) for s in missing_canonical],
        "resume_skills": [display_skill(s) for s in resume_skills],
        "jd_skills": [display_skill(s) for s in jd_skills],
    }
