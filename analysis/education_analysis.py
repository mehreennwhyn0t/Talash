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
    enriched = []

    for record in education_records:
        degree = record.get("degree", "")
        grade = record.get("grade", "")
        institution = record.get("institution", "")
        year = record.get("year", "")

        specialization = extract_specialization_from_degree(degree)

        enriched_record = {
            **record,
            "education_level": classify_education_level(degree),
            "score_original": grade,
            "score_type": detect_score_type(grade),
            "score_normalized_100": normalize_score_to_100(grade),
            "specialization_inferred": specialization if specialization else "N/A",
            "institution_clean": " ".join(str(institution).split()) if institution else "N/A",
            "year_int": safe_int(year),
        }
        enriched.append(enriched_record)

    return enriched


def sort_education_timeline(education_records: List[Dict]) -> List[Dict]:
    return sorted(education_records, key=sort_education_key)


def build_normalized_scores(ordered_records: List[Dict]) -> List[Dict]:
    return [
        {
            "degree": record.get("degree", "N/A"),
            "education_level": record.get("education_level", "N/A"),
            "institution": record.get("institution_clean", "N/A"),
            "year": record.get("year", "N/A"),
            "score_original": record.get("score_original", "N/A"),
            "score_type": record.get("score_type", "N/A"),
            "score_normalized_100": (
                record.get("score_normalized_100")
                if record.get("score_normalized_100") is not None
                else "N/A"
            ),
        }
        for record in ordered_records
    ]


def build_education_table(ordered_records: List[Dict]) -> List[Dict]:
    table = []

    for record in ordered_records:
        table.append(
            {
                "Degree": record.get("degree", "N/A"),
                "Level": record.get("education_level", "N/A"),
                "Institution": record.get("institution_clean", "N/A"),
                "Year": record.get("year", "N/A"),
                "Score": record.get("score_original", "N/A"),
                "Normalized Score (/100)": (
                    record.get("score_normalized_100")
                    if record.get("score_normalized_100") is not None
                    else "N/A"
                ),
                "Specialization": record.get("specialization_inferred", "N/A"),
            }
        )

    return table


def build_gap_table(gaps: List[Dict]) -> List[Dict]:
    if not gaps:
        return [
            {
                "After Degree": "N/A",
                "Before Degree": "N/A",
                "Gap Years": 0,
                "Status": "No major gaps detected",
                "Reason": "N/A",
            }
        ]

    return [
        {
            "After Degree": gap.get("after_degree", "N/A"),
            "Before Degree": gap.get("before_degree", "N/A"),
            "Gap Years": gap.get("gap_years", "N/A"),
            "Status": gap.get("status", "N/A"),
            "Reason": gap.get("reason", "N/A"),
        }
        for gap in gaps
    ]


def detect_education_gaps(ordered_records: List[Dict]) -> List[Dict]:
    gaps = []

    for i in range(len(ordered_records) - 1):
        current = ordered_records[i]
        next_rec = ordered_records[i + 1]

        y1 = current.get("year_int")
        y2 = next_rec.get("year_int")

        if y1 is None or y2 is None:
            continue

        diff = y2 - y1

        if diff > 3:
            gaps.append(
                {
                    "after_degree": current.get("degree", ""),
                    "before_degree": next_rec.get("degree", ""),
                    "gap_years": diff,
                    "status": "requires_review",
                    "reason": "Large year difference between consecutive education records",
                }
            )

    return gaps


def analyze_progression(ordered_records: List[Dict]) -> str:
    scores = [
        r.get("score_normalized_100")
        for r in ordered_records
        if r.get("score_normalized_100") is not None
    ]

    if len(scores) == 0:
        return "no_scores_available"

    if len(scores) < 2:
        return "insufficient_data"

    pos, neg = 0, 0

    for i in range(len(scores) - 1):
        if scores[i + 1] > scores[i]:
            pos += 1
        elif scores[i + 1] < scores[i]:
            neg += 1

    if pos > 0 and neg == 0:
        return "improving"
    if neg > 0 and pos == 0:
        return "declining"
    if pos > 0 and neg > 0:
        return "mixed"

    return "stable"


def check_specialization_consistency(ordered_records: List[Dict]) -> str:
    texts = []

    for r in ordered_records:
        if r.get("education_level") in HIGHER_ED_LEVELS:
            text = (
                str(r.get("degree", "")) + " " + str(r.get("specialization_inferred", ""))
            ).lower()
            texts.append(text)

    if len(texts) < 2:
        return "insufficient_data"

    keywords = {
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

    sets = []
    for t in texts:
        sets.append({k for k in keywords if k in t})

    common = set.intersection(*sets) if sets else set()

    return "mostly_consistent" if len(common) >= 1 else "unclear"


def build_gap_summary(gaps: List[Dict]) -> str:
    if not gaps:
        return "No major education timeline gaps detected."
    return f"{len(gaps)} education timeline gap(s) require review."


def generate_education_summary(
    ordered_records: List[Dict],
    progression_label: str,
    specialization_consistency: str,
    gaps: List[Dict],
) -> str:

    if not ordered_records:
        return "No education records were available for analysis."

    highest = ordered_records[-1]
    degree = highest.get("degree", "")
    inst = highest.get("institution_clean", "")
    year = highest.get("year", "")

    parts = [f"The candidate's highest detected qualification is {degree}"]

    if inst and inst != "N/A":
        parts[-1] += f" from {inst}"
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
        parts.append("Academic performance appears stable across stages.")
    elif progression_label == "no_scores_available":
        parts.append("Academic performance could not be evaluated due to missing scores.")

    if specialization_consistency == "mostly_consistent":
        parts.append("The candidate demonstrates a generally consistent academic specialization pathway.")
    elif specialization_consistency == "unclear":
        parts.append("Specialization consistency is unclear from the available records.")

    parts.append(build_gap_summary(gaps))

    return " ".join(parts)


def build_education_highlights(
    ordered_records: List[Dict],
    progression_label: str,
    specialization_consistency: str,
    gaps: List[Dict],
) -> Dict:
    highest_record = ordered_records[-1] if ordered_records else {}

    return {
        "highest_degree": highest_record.get("degree", "N/A"),
        "highest_institution": highest_record.get("institution_clean", "N/A"),
        "highest_year": highest_record.get("year", "N/A"),
        "progression_label": progression_label,
        "specialization_consistency": specialization_consistency,
        "gap_count": len(gaps),
    }


def analyze_education_profile(profile: Dict) -> Dict:
    education_records = profile.get("education", [])

    enriched = enrich_education_records(education_records)
    ordered = sort_education_timeline(enriched)

    normalized_scores = build_normalized_scores(ordered)
    education_table = build_education_table(ordered)

    gaps = detect_education_gaps(ordered)
    gap_table = build_gap_table(gaps)

    progression = analyze_progression(ordered)
    consistency = check_specialization_consistency(ordered)
    gap_summary = build_gap_summary(gaps)

    summary = generate_education_summary(
        ordered, progression, consistency, gaps
    )

    highlights = build_education_highlights(
        ordered, progression, consistency, gaps
    )

    return {
        "ordered_timeline": ordered,
        "education_table": education_table,
        "gap_table": gap_table,
        "normalized_scores": normalized_scores,
        "progression_label": progression,
        "specialization_consistency": consistency,
        "gaps": gaps,
        "gap_summary": gap_summary,
        "gap_justification": [],
        "institution_quality": [],
        "education_highlights": highlights,
        "education_summary": summary,
    }