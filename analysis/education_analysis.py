from typing import Dict, List

from analysis.normalizers import (
    classify_education_level,
    detect_score_type,
    normalize_score_to_100,
    extract_specialization_from_degree,
    safe_int,
    sort_education_key,
)


def enrich_education_records(education_records: List[Dict]) -> List[Dict]:
    """
    Add analysis-friendly fields to parsed education records.
    """
    enriched = []

    for record in education_records:
        degree = record.get("degree", "")
        grade = record.get("grade", "")
        institution = record.get("institution", "")
        year = record.get("year", "")

        enriched_record = {
            **record,
            "education_level": classify_education_level(degree),
            "score_original": grade,
            "score_type": detect_score_type(grade),
            "score_normalized_100": normalize_score_to_100(grade),
            "specialization_inferred": extract_specialization_from_degree(degree),
            "institution_clean": " ".join(str(institution).split()),
            "year_int": safe_int(year),
        }
        enriched.append(enriched_record)

    return enriched


def sort_education_timeline(education_records: List[Dict]) -> List[Dict]:
    """
    Sort education from SSC -> highest degree.
    """
    return sorted(education_records, key=sort_education_key)


def build_normalized_scores(ordered_records: List[Dict]) -> List[Dict]:
    """
    Create compact normalized score view for UI/table use.
    """
    return [
        {
            "degree": record.get("degree", ""),
            "education_level": record.get("education_level", ""),
            "institution": record.get("institution_clean", ""),
            "year": record.get("year", ""),
            "score_original": record.get("score_original", ""),
            "score_type": record.get("score_type", ""),
            "score_normalized_100": record.get("score_normalized_100"),
        }
        for record in ordered_records
    ]


def detect_education_gaps(ordered_records: List[Dict]) -> List[Dict]:
    """
    Basic gap detection using consecutive education completion years.
    This is a Milestone 2 starter version.
    """
    gaps = []

    for i in range(len(ordered_records) - 1):
        current_record = ordered_records[i]
        next_record = ordered_records[i + 1]

        current_year = current_record.get("year_int")
        next_year = next_record.get("year_int")

        if current_year is None or next_year is None:
            continue

        # Simple heuristic:
        # if next degree completion year is more than 3 years after current,
        # flag a potential education gap
        year_diff = next_year - current_year

        if year_diff > 3:
            gaps.append(
                {
                    "after_degree": current_record.get("degree", ""),
                    "before_degree": next_record.get("degree", ""),
                    "gap_years": year_diff,
                    "status": "potential_gap",
                }
            )

    return gaps


def analyze_progression(ordered_records: List[Dict]) -> str:
    """
    Basic performance trend using normalized scores only.
    """
    scores = [
        record.get("score_normalized_100")
        for record in ordered_records
        if record.get("score_normalized_100") is not None
    ]

    if len(scores) < 2:
        return "insufficient_data"

    if scores[-1] > scores[0]:
        return "improving"
    if scores[-1] < scores[0]:
        return "declining"
    return "stable"


def check_specialization_consistency(ordered_records: List[Dict]) -> str:
    """
    Lightweight check whether UG/PG/PhD seem topically related.
    """
    higher_ed = [
        record.get("degree", "").lower()
        for record in ordered_records
        if record.get("education_level") in {"UG", "PG", "PhD"}
    ]

    if len(higher_ed) < 2:
        return "insufficient_data"

    keywords = [
        "electrical",
        "computer",
        "telecom",
        "communication",
        "electronics",
        "software",
        "data",
        "ai",
        "machine learning",
        "network",
    ]

    matched_keywords = set()
    for degree in higher_ed:
        for keyword in keywords:
            if keyword in degree:
                matched_keywords.add(keyword)

    if len(matched_keywords) >= 1:
        return "mostly_consistent"

    return "unclear"


def generate_education_summary(
    ordered_records: List[Dict],
    progression_label: str,
    specialization_consistency: str,
    gaps: List[Dict],
) -> str:
    """
    Generate a concise rule-based summary.
    """
    if not ordered_records:
        return "No education records were available for analysis."

    highest_degree = ordered_records[-1].get("degree", "Unknown highest degree")
    institution = ordered_records[-1].get("institution_clean", "")
    year = ordered_records[-1].get("year", "")

    parts = [
        f"The candidate's highest detected qualification is {highest_degree}"
    ]

    if institution:
        parts[-1] += f" from {institution}"
    if year:
        parts[-1] += f" ({year})"

    parts[-1] += "."

    if progression_label != "insufficient_data":
        parts.append(f"Academic performance trend appears {progression_label}.")

    if specialization_consistency != "insufficient_data":
        if specialization_consistency == "mostly_consistent":
            parts.append("The academic pathway appears broadly consistent in specialization.")
        else:
            parts.append("Specialization consistency is unclear from the available records.")

    if gaps:
        parts.append(f"{len(gaps)} potential education gap(s) were detected and should be reviewed.")
    else:
        parts.append("No major educational gaps were detected from the available completion years.")

    return " ".join(parts)


def analyze_education_profile(profile: Dict) -> Dict:
    """
    Main entry point for Milestone 2 education analysis.
    Input: parsed candidate profile
    Output: structured education analysis block
    """
    education_records = profile.get("education", [])

    enriched_records = enrich_education_records(education_records)
    ordered_timeline = sort_education_timeline(enriched_records)
    normalized_scores = build_normalized_scores(ordered_timeline)
    gaps = detect_education_gaps(ordered_timeline)
    progression_label = analyze_progression(ordered_timeline)
    specialization_consistency = check_specialization_consistency(ordered_timeline)

    education_summary = generate_education_summary(
        ordered_records=ordered_timeline,
        progression_label=progression_label,
        specialization_consistency=specialization_consistency,
        gaps=gaps,
    )

    return {
        "ordered_timeline": ordered_timeline,
        "normalized_scores": normalized_scores,
        "progression_label": progression_label,
        "specialization_consistency": specialization_consistency,
        "gaps": gaps,
        "gap_justification": [],
        "institution_quality": [],
        "education_summary": education_summary,
    }