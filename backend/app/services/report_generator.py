"""
Build a markdown-style text report from match results and bullets.
"""


def generate_report(
    match_result: dict,
    rewritten_bullets: list[str],
    llm_success: bool = True,
    cover_letter: str = "",
    cover_letter_success: bool = True,
    technical_questions: list[str] | None = None,
    behavioral_questions: list[str] | None = None,
    study_topics: list[str] | None = None,
    interview_prep_success: bool = True,
) -> str:
    """
    Assemble a readable report for the frontend / API response.

    Args:
        match_result: Output from match_resume_to_jd.
        rewritten_bullets: Bullets from LLM or fallback generator.
        llm_success: False when fallback bullets were used.
    """
    score = match_result["match_score"]
    matched = match_result["matched_skills"]
    missing = match_result["missing_skills"]
    resume_skills = match_result.get("resume_skills", [])
    jd_skills = match_result.get("jd_skills", [])

    matched_lines = (
        "\n".join(f"- {skill}" for skill in matched) if matched else "- None detected"
    )
    missing_lines = (
        "\n".join(f"- {skill}" for skill in missing) if missing else "- None — great match!"
    )
    bullet_lines = "\n".join(f"- {b}" for b in rewritten_bullets)

    improvements: list[str] = []
    if not llm_success:
        improvements.append(
            "AI optimization temporarily unavailable. "
            "Fallback resume suggestions were generated."
        )
    if missing:
        improvements.append(
            f"Add project examples that mention: {', '.join(missing[:5])}."
        )
    if not resume_skills:
        improvements.append(
            "List concrete tools and frameworks in your resume (not only soft skills)."
        )
    if not jd_skills:
        improvements.append(
            "The job description had no recognized skills — paste a fuller JD with tech keywords."
        )
    if score < 50 and missing:
        improvements.append(
            "Prioritize upskilling or coursework in the top missing skills before applying."
        )
    if not improvements:
        improvements.append("Resume keywords align well with this job description.")

    improvement_text = "\n".join(f"- {line}" for line in improvements)

    fallback_notice = ""
    if not llm_success:
        fallback_notice = (
            "_AI optimization temporarily unavailable. "
            "Fallback resume suggestions were generated._\n\n"
        )

    cover_letter_section = ""
    if cover_letter:
        cl_notice = (
            "_AI cover letter generation was temporarily unavailable. "
            "A fallback draft was generated._\n\n"
            if not cover_letter_success
            else ""
        )
        cover_letter_section = f"\n## Cover Letter\n{cl_notice}{cover_letter}\n"

    interview_prep_section = ""
    tech_qs = technical_questions or []
    behav_qs = behavioral_questions or []
    topics = study_topics or []
    if tech_qs or behav_qs or topics:
        ip_notice = (
            "_AI interview prep generation was temporarily unavailable. "
            "Fallback suggestions were generated._\n\n"
            if not interview_prep_success
            else ""
        )
        tech_lines = "\n".join(f"- {q}" for q in tech_qs)
        behav_lines = "\n".join(f"- {q}" for q in behav_qs)
        topic_lines = "\n".join(f"- {t}" for t in topics)
        interview_prep_section = (
            f"\n## Interview Prep\n{ip_notice}"
            f"### Technical Questions\n{tech_lines}\n\n"
            f"### Behavioral Questions\n{behav_lines}\n\n"
            f"### Study Topics\n{topic_lines}\n"
        )

    return f"""# Job Match Report

{fallback_notice}## Match Score
**{score} / 100**

## Matched Skills
{matched_lines}

## Missing Skills
{missing_lines}

## Suggested Improvements
{improvement_text}

## Rewritten Resume Bullets
{bullet_lines}
{cover_letter_section}{interview_prep_section}"""
