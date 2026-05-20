"""
Build a markdown-style text report from match results and bullets.
"""


def generate_report(
    match_result: dict,
    rewritten_bullets: list[str],
) -> str:
    """
    Assemble a readable report for the frontend / API response.

    Args:
        match_result: Output from match_resume_to_jd (display-name lists).
        rewritten_bullets: Template bullets from bullet_rewriter.
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

    return f"""# Job Match Report

                ## Match Score
                **{score} / 100**

                ## Matched Skills
                {matched_lines}

                ## Missing Skills
                {missing_lines}

                ## Suggested Improvements
                {improvement_text}

                ## Rewritten Resume Bullets
                {bullet_lines}
            """
