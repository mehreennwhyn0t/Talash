from typing import Dict, List

from analysis.normalizers import (
    classify_education_level,
    detect_score_type,
    normalize_score_to_100,
    extract_specialization_from_degree,
    safe_int,
    sort_education_key,
)


HIGHER_ED_LEVELS = {"UG", "PG", "PhD"}


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
    This is still a starter version for Milestone 2.
    """
    gaps = []

    for i in range(len(ordered_records) - 1):
        current_record = ordered_records[i]
        next_record = ordered_records[i + 1]

        current_year = current_record.get("year_int")
        next_year = next_record.get("year_int")

        if current_year is None or next_year is None:
            continue

        year_diff = next_year - current_year

        # More than 3 years between consecutive degree completion years
        # is flagged for review.
        if year_diff > 3:
            gaps.append(
                {
                    "after_degree": current_record.get("degree", ""),
                    "before_degree": next_record.get("degree", ""),
                    "gap_years": year_diff,
                    "status": "requires_review",
                    "reason": "Large year difference between consecutive education records",
                }
            )

    return gaps


def analyze_progression(ordered_records: List[Dict]) -> str:
    """
    Improved progression logic using consecutive normalized scores.
    """
    scores = [
        record.get("score_normalized_100")
        for record in ordered_records
        if record.get("score_normalized_100") is not None
    ]

    if len(scores) < 2:
        return "insufficient_data"

    positive_steps = 0
    negative_steps = 0

    for i in range(len(scores) - 1):
        if scores[i + 1] > scores[i]:
            positive_steps += 1
        elif scores[i + 1] < scores[i]:
            negative_steps += 1

    if positive_steps > 0 and negative_steps == 0:
        return "improving"

    if negative_steps > 0 and positive_steps == 0:
        return "declining"

    if positive_steps > 0 and negative_steps > 0:
        return "mixed"

    return "stable"


def check_specialization_consistency(ordered_records: List[Dict]) -> str:
    """
    Check whether UG/PG/PhD appear broadly aligned by domain keywords.
    """
    higher_ed_text = []

    for record in ordered_records:
        if record.get("education_level") in HIGHER_ED_LEVELS:
            combined_text = " ".join(
                [
                    str(record.get("degree", "")),
                    str(record.get("specialization_inferred", "")),
                ]
            ).lower()
            higher_ed_text.append(combined_text)

    if len(higher_ed_text) < 2:
        return "insufficient_data"

    domain_keywords = {
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
        "systems",
    }

    matched_counts = []
    for text in higher_ed_text:
        matched = {keyword for keyword in domain_keywords if keyword in text}
        matched_counts.append(matched)

    common_keywords = set.intersection(*matched_counts) if matched_counts else set()

    if len(common_keywords) >= 1:
        return "mostly_consistent"

    return "unclear"


def build_gap_summary(gaps: List[Dict]) -> str:
    """
    Convert gap list into a simple readable label.
    """
    if not gaps:
        return "No major education timeline gaps detected."

    return f"{len(gaps)} education timeline gap(s) require review."


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

    if progression_label == "improving":
        parts.append("Academic performance trend appears improving.")
    elif progression_label == "declining":
        parts.append("Academic performance trend appears declining.")
    elif progression_label == "mixed":
        parts.append("Academic performance trend appears mixed across educational stages.")
    elif progression_label == "stable":
        parts.append("Academic performance appears broadly stable across available educational stages.")

    if specialization_consistency != "insufficient_data":
        if specialization_consistency == "mostly_consistent":
            parts.append("The candidate demonstrates a generally consistent academic specialization pathway.")
        else:
            parts.append("Specialization consistency is unclear from the available education records.")

    parts.append(build_gap_summary(gaps))

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
    gap_summary = build_gap_summary(gaps)

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
        "gap_summary": gap_summary,
        "gap_justification": [],
        "institution_quality": [],
        "education_summary": education_summary,
    }