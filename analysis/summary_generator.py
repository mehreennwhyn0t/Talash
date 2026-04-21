# analysis/summary_generator.py

def generate_summary(education, experience, research, missing):
    """
    Combines education, experience, research, and missing info
    to generate a simple candidate summary.
    """

    # ======================
    # 1. Strengths
    # ======================
    strengths = []

    # Research strength
    if research.get("total_publications", 0) >= 3:
        strengths.append("Strong research profile with multiple publications")

    # Education strength
    if education.get("progression_label") == "improving":
        strengths.append("Improving academic performance")

    # Experience strength
    if len(experience.get("employment_gaps", [])) == 0:
        strengths.append("Consistent professional experience")

    # ======================
    # 2. Concerns
    # ======================
    concerns = []

    # Missing information
    if len(missing.get("missing", [])) > 0:
        concerns.append("Missing important information in CV")

    # Experience gaps
    if len(experience.get("employment_gaps", [])) > 0:
        concerns.append("Employment gaps detected")

    # Low research output
    if research.get("total_publications", 0) == 0:
        concerns.append("No research publications found")

    # ======================
    # 3. Suitability Label
    # ======================
    if len(concerns) == 0:
        label = "Strong Candidate"
    elif len(concerns) <= 2:
        label = "Moderate Candidate"
    else:
        label = "Needs Review"

    # ======================
    # 4. Overall Assessment (Simple Text)
    # ======================
    assessment = "This candidate shows "

    if len(strengths) > 0:
        assessment += ", ".join(strengths)
    else:
        assessment += "limited strengths"

    if len(concerns) > 0:
        assessment += ". However, " + ", ".join(concerns)

    assessment += "."

    # ======================
    # 5. Final Output
    # ======================
    return {
        "strengths": strengths,
        "concerns": concerns,
        "suitability_label": label,
        "overall_assessment": assessment
    }