"""
summary_generator.py

Candidate summary and assessment generation.
Generates both rule-based and LLM-enhanced candidate summaries.
"""


def generate_summary(education, experience, research, missing):
    """
    Generate a comprehensive candidate summary using rule-based logic.
    Falls back gracefully when LLM is unavailable.
    """

    # Strengths
    strengths = []

    # Research strength
    total_pubs = research.get("total_publications", 0)
    if total_pubs >= 10:
        strengths.append(f"Strong research profile with {total_pubs} publications")
    elif total_pubs >= 5:
        strengths.append(f"Solid research output with {total_pubs} publications")
    elif total_pubs >= 3:
        strengths.append(f"Active researcher with {total_pubs} publications")

    # Journal quality
    if research.get("venue_analysis", {}).get("avg_impact_factor"):
        avg_if = research["venue_analysis"]["avg_impact_factor"]
        if avg_if >= 3.0:
            strengths.append(f"High-quality publication venues (avg IF: {avg_if})")
        elif avg_if >= 1.5:
            strengths.append(f"Respectable publication venues (avg IF: {avg_if})")

    # First author publications
    if research.get("first_author_count", 0) >= 2:
        strengths.append(
            f"{research['first_author_count']} first-author publications "
            f"demonstrating research leadership"
        )

    # Education strength
    prog = education.get("progression_trend", "")
    if prog == "improving":
        strengths.append("Improving academic performance across educational levels")
    if education.get("academic_strength") == "strong":
        strengths.append("Strong academic credentials")
    if education.get("highest_qualification", "").lower().startswith("phd"):
        strengths.append("Holds a PhD - highest academic qualification")

    # Experience strength
    total_years = experience.get("total_experience_years", 0)
    if total_years >= 10:
        strengths.append(f"Extensive professional experience ({total_years} years)")
    elif total_years >= 5:
        strengths.append(f"Solid professional experience ({total_years} years)")

    if len(experience.get("employment_gaps", [])) == 0:
        strengths.append("Consistent employment history with no gaps")

    career_prog = experience.get("career_progression_label", "")
    if "upward" in career_prog.lower():
        strengths.append(f"Career trajectory: {career_prog}")

    # Specialization
    if education.get("specialization_consistency") == "consistent":
        strengths.append("Consistent academic specialization across degrees")

    # Concerns
    concerns = []

    # Missing information
    total_missing = missing.get("total_issues", 0)
    if total_missing == 0:
        total_missing = (
            len(missing.get("missing", [])) +
            len(missing.get("incomplete", [])) +
            len(missing.get("unclear", []))
        )
    if total_missing > 5:
        concerns.append(f"Significant amount of missing/incomplete information ({total_missing} issues)")
    elif total_missing > 0:
        concerns.append(f"Some missing information in CV ({total_missing} issues)")

    # Employment gaps
    sig_gaps = [
        g for g in experience.get("employment_gaps", [])
        if g.get("severity") == "significant"
    ]
    if sig_gaps:
        concerns.append(
            f"{len(sig_gaps)} significant employment gap(s) detected"
        )

    # Job overlaps
    overlaps = experience.get("job_overlaps", [])
    serious_overlaps = [o for o in overlaps if o.get("overlap_months", 0) > 3]
    if serious_overlaps:
        concerns.append(
            f"{len(serious_overlaps)} overlapping employment period(s) need clarification"
        )

    # Low research output
    if total_pubs == 0:
        concerns.append("No research publications found")
    elif total_pubs < 3:
        concerns.append("Limited research output")

    # Educational gaps
    unjustified_gaps = [
        g for g in education.get("educational_gaps", [])
        if not g.get("justified")
    ]
    if unjustified_gaps:
        concerns.append(
            f"{len(unjustified_gaps)} unexplained educational gap(s)"
        )

    # Declining performance
    if prog == "declining":
        concerns.append("Declining academic performance trend")

    # Suitability Label
    strength_score = len(strengths)
    concern_score = len(concerns)

    if concern_score == 0 and strength_score >= 3:
        label = "Strong Candidate"
    elif concern_score <= 2 and strength_score >= 2:
        label = "Good Candidate"
    elif concern_score <= 3:
        label = "Moderate Candidate"
    else:
        label = "Needs Review"

    # Overall Assessment
    assessment_parts = []

    if strengths:
        assessment_parts.append(
            f"This candidate demonstrates: {', '.join(strengths[:3]).lower()}"
        )
    else:
        assessment_parts.append("This candidate shows limited distinguishing strengths")

    if concerns:
        assessment_parts.append(
            f"However, there are some concerns: {', '.join(concerns[:3]).lower()}"
        )
    else:
        assessment_parts.append("No significant concerns were identified")

    # Key highlights
    highlights = []
    if education.get("highest_qualification"):
        highlights.append(
            f"Highest qualification: {education['highest_qualification']}"
        )
    if total_years > 0:
        highlights.append(f"Total experience: {total_years} years")
    if total_pubs > 0:
        highlights.append(f"Publications: {total_pubs}")
    if research.get("dominant_theme"):
        highlights.append(f"Research focus: {research['dominant_theme']}")

    assessment = ". ".join(assessment_parts) + "."

    return {
        "strengths":          strengths,
        "concerns":           concerns,
        "suitability_label":  label,
        "overall_assessment": assessment,
        "key_highlights":     highlights,
        "strength_count":     strength_score,
        "concern_count":      concern_score,
    }


def generate_llm_summary(profile, education, experience, research, missing):
    """
    Generate an LLM-enhanced candidate summary using Gemini.
    Falls back to rule-based summary on failure.
    """
    try:
        from llm.gemini_client import call_gemini, is_api_available
        from llm.prompts import candidate_summary_prompt

        if not is_api_available():
            return generate_summary(education, experience, research, missing)

        name = profile.get("personal_information", {}).get("name", "Unknown")
        prompt = candidate_summary_prompt(
            name, education, experience, research, missing
        )
        result = call_gemini(prompt, expect_json=True)

        if isinstance(result, dict) and not result.get("parse_error"):
            # Ensure required keys
            for key in ["strengths", "concerns", "suitability_label",
                        "overall_assessment", "key_highlights"]:
                if key not in result:
                    result[key] = []
            return result

    except Exception as e:
        print(f"[TALASH] LLM summary failed, using rule-based: {e}")

    return generate_summary(education, experience, research, missing)