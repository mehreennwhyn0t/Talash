"""
education_analysis.py

Full educational profile analysis.
Covers: score normalization, education level classification, gap detection,
progression analysis, institution quality, and overall strength interpretation.
"""

import re
from analysis.normalizers import (
    classify_education_level,
    detect_score_type,
    normalize_score_to_100,
    extract_specialization_from_degree,
    sort_education_key,
    safe_int,
    LEVEL_ORDER,
)


# Known university rankings (simplified lookup)
# In a production system, this would query THE/QS APIs.
# For Milestone 2, we use a curated lookup of Pakistani & regional universities.
UNIVERSITY_TIERS = {
    # Tier 1 - QS/THE ranked, internationally recognized
    "nust": {"tier": 1, "label": "Highly Ranked (QS Top 500)", "qs_range": "400-500"},
    "national university of sciences and technology": {"tier": 1, "label": "Highly Ranked (QS Top 500)", "qs_range": "400-500"},
    "lums": {"tier": 1, "label": "Highly Ranked", "qs_range": "500-700"},
    "lahore university of management sciences": {"tier": 1, "label": "Highly Ranked", "qs_range": "500-700"},
    "quaid-i-azam university": {"tier": 1, "label": "Highly Ranked", "qs_range": "400-500"},
    "aga khan university": {"tier": 1, "label": "Highly Ranked", "qs_range": "200-300"},
    "comsats": {"tier": 2, "label": "Well Ranked", "qs_range": "700-900"},
    "comsats university": {"tier": 2, "label": "Well Ranked", "qs_range": "700-900"},
    "pieas": {"tier": 1, "label": "Highly Ranked", "qs_range": "500-700"},
    "giki": {"tier": 2, "label": "Well Ranked", "qs_range": "700-900"},
    "ist": {"tier": 2, "label": "Well Ranked", "qs_range": "Not Ranked"},
    "institute of space technology": {"tier": 2, "label": "Well Ranked", "qs_range": "Not Ranked"},
    "international islamic university": {"tier": 2, "label": "Well Ranked", "qs_range": "700-1000"},
    "uet lahore": {"tier": 2, "label": "Well Ranked", "qs_range": "600-800"},
    "ned university": {"tier": 2, "label": "Well Ranked", "qs_range": "700-900"},
    # Tier 3 - Recognized, not in major rankings
    "foundation university": {"tier": 3, "label": "Recognized", "qs_range": "Not Ranked"},
    "bahria university": {"tier": 3, "label": "Recognized", "qs_range": "Not Ranked"},
    "air university": {"tier": 3, "label": "Recognized", "qs_range": "Not Ranked"},
    "fast": {"tier": 2, "label": "Well Ranked", "qs_range": "Not Ranked"},
    "center for advanced studies": {"tier": 2, "label": "Well Ranked", "qs_range": "Not Ranked"},
    # Tier 4 - Smaller / less known
    "qurtuba university": {"tier": 4, "label": "Recognized (Regional)", "qs_range": "Not Ranked"},
    # International
    "xi'an international university": {"tier": 3, "label": "Recognized (International)", "qs_range": "Not Ranked"},
    "mit": {"tier": 1, "label": "World-Class (QS Top 5)", "qs_range": "1-5"},
    "stanford": {"tier": 1, "label": "World-Class (QS Top 10)", "qs_range": "1-10"},
    "oxford": {"tier": 1, "label": "World-Class (QS Top 10)", "qs_range": "1-10"},
    "cambridge": {"tier": 1, "label": "World-Class (QS Top 10)", "qs_range": "1-10"},
}


def lookup_institution_quality(institution_name: str) -> dict:
    """Look up institution quality from known rankings."""
    if not institution_name:
        return {"tier": None, "label": "Unknown", "qs_range": "Not Available"}

    name_lower = institution_name.lower().strip()

    # Direct match
    if name_lower in UNIVERSITY_TIERS:
        return UNIVERSITY_TIERS[name_lower]

    # Partial match
    for key, value in UNIVERSITY_TIERS.items():
        if key in name_lower or name_lower in key:
            return value

    return {"tier": None, "label": "Not in database", "qs_range": "Not Available"}


def interpret_score(normalized_score, level):
    """Interpret a normalized score (out of 100)."""
    if normalized_score is None:
        return "N/A"
    if normalized_score >= 85:
        return "excellent"
    elif normalized_score >= 70:
        return "good"
    elif normalized_score >= 55:
        return "average"
    else:
        return "below_average"


def analyze_education_profile(profile: dict) -> dict:
    """
    Full educational profile analysis.
    Performs: classification, normalization, gap detection, progression,
    institution ranking lookup, and overall assessment.
    """
    education_records = profile.get("education", [])
    experience_records = profile.get("experience", [])

    if not education_records:
        return {
            "education_table": [],
            "education_levels": [],
            "degree_sequence": "No education data",
            "academic_pathway": "unknown",
            "progression_trend": "unknown",
            "highest_qualification": "Unknown",
            "specialization_consistency": "unknown",
            "specialization_summary": "No data available",
            "educational_gaps": [],
            "total_gap_years": 0,
            "academic_strength": "unknown",
            "interpretation": "No education records found in the CV.",
            "education_summary": "No education data available.",
            "institution_quality": [],
        }

    # Step 1: Classify and normalize each record
    enriched = []
    for rec in education_records:
        degree = rec.get("degree", "")
        grade = rec.get("grade", "")
        year = rec.get("year", "") or rec.get("end_year", "")
        institution = rec.get("institution", "")
        specialization = rec.get("specialization", "") or extract_specialization_from_degree(degree)

        level = classify_education_level(degree)
        score_type = detect_score_type(grade)
        normalized = normalize_score_to_100(grade)
        year_int = safe_int(year)
        inst_quality = lookup_institution_quality(institution)

        enriched.append({
            "degree": degree,
            "specialization": specialization,
            "institution": institution,
            "original_score": grade,
            "score_type": score_type,
            "normalized_score": normalized,
            "score_interpretation": interpret_score(normalized, level),
            "year": year,
            "year_int": year_int,
            "education_level": level,
            "institution_quality": inst_quality,
        })

    # Sort by education level then year
    enriched.sort(key=sort_education_key)

    # Step 2: Build degree sequence
    degree_names = []
    for e in enriched:
        label = e["education_level"]
        if label != "Unknown":
            degree_names.append(f"{label} ({e['degree']})")
        else:
            degree_names.append(e["degree"])
    degree_sequence = " to ".join(degree_names)

    # Step 3: Identify highest qualification
    level_priority = {"PhD": 5, "PG": 4, "UG": 3, "HSSC": 2, "SSC": 1, "Unknown": 0}
    highest = max(enriched, key=lambda x: level_priority.get(x["education_level"], 0))
    highest_qualification = highest["degree"]

    # Step 4: Detect educational gaps
    gaps = []
    dated_records = [e for e in enriched if e["year_int"] is not None]
    for i in range(1, len(dated_records)):
        prev = dated_records[i - 1]
        curr = dated_records[i]
        gap = curr["year_int"] - prev["year_int"]

        expected_duration = {
            ("SSC", "HSSC"): 2,
            ("HSSC", "UG"): 4,
            ("UG", "PG"): 2,
            ("PG", "PhD"): 4,
        }
        key = (prev["education_level"], curr["education_level"])
        expected = expected_duration.get(key, 3)

        if gap > expected + 1:  # More than 1 year beyond expected
            actual_gap = gap - expected
            # Check if justified by work experience
            justified = False
            justification = ""
            for exp in experience_records:
                exp_start = safe_int(exp.get("start_year", ""))
                exp_end_str = exp.get("end_year", "")
                if exp_end_str and exp_end_str.lower() == "present":
                    from datetime import datetime
                    exp_end = datetime.now().year
                else:
                    exp_end = safe_int(exp_end_str)

                if exp_start and exp_end:
                    if exp_start <= curr["year_int"] and exp_end >= prev["year_int"]:
                        justified = True
                        justification = f"Working as {exp.get('title', 'N/A')} at {exp.get('organization', 'N/A')}"
                        break

            gaps.append({
                "between": f"{prev['degree']} to {curr['degree']}",
                "from_year": prev["year_int"],
                "to_year": curr["year_int"],
                "gap_years": actual_gap,
                "justified": justified,
                "justification": justification if justified else "No justification found",
            })

    total_gap_years = sum(g["gap_years"] for g in gaps)

    # Step 5: Analyze progression trend
    scores = [e["normalized_score"] for e in enriched if e["normalized_score"] is not None]
    if len(scores) >= 2:
        first_half = scores[:len(scores)//2]
        second_half = scores[len(scores)//2:]
        avg_first = sum(first_half) / len(first_half)
        avg_second = sum(second_half) / len(second_half)
        diff = avg_second - avg_first
        if diff > 5:
            progression_trend = "improving"
        elif diff < -5:
            progression_trend = "declining"
        else:
            progression_trend = "stable"
    else:
        progression_trend = "insufficient_data"

    # Step 6: Specialization consistency
    specializations = [
        e["specialization"].lower() for e in enriched
        if e["specialization"] and e["education_level"] in ("UG", "PG", "PhD")
    ]
    if len(specializations) >= 2:
        # Simple check: do they share common words?
        word_sets = [set(s.split()) for s in specializations]
        common = word_sets[0]
        for ws in word_sets[1:]:
            common = common & ws
        if len(common) > 0:
            spec_consistency = "consistent"
            spec_summary = f"Consistent focus on: {', '.join(specializations)}"
        else:
            # Check for related fields
            all_words = set()
            for ws in word_sets:
                all_words.update(ws)
            related_clusters = {
                "electrical", "electronics", "telecom", "telecommunication",
                "communication", "signal", "wireless", "power"
            }
            overlap = all_words & related_clusters
            if len(overlap) >= 2:
                spec_consistency = "partially_consistent"
                spec_summary = f"Related fields: {', '.join(specializations)}"
            else:
                spec_consistency = "inconsistent"
                spec_summary = f"Diverse fields: {', '.join(specializations)}"
    else:
        spec_consistency = "insufficient_data"
        spec_summary = "Not enough higher education records to assess"

    # Step 7: Academic pathway type
    levels_present = [e["education_level"] for e in enriched]
    if "PhD" in levels_present and "PG" in levels_present and "UG" in levels_present:
        pathway = "complete_research_track"
    elif "PG" in levels_present and "UG" in levels_present:
        pathway = "standard_postgraduate"
    elif "UG" in levels_present:
        pathway = "undergraduate_only"
    else:
        pathway = "non_standard"

    # Step 8: Academic strength assessment
    avg_score = sum(scores) / len(scores) if scores else 0
    if avg_score >= 80 and "PhD" in levels_present:
        strength = "strong"
    elif avg_score >= 65 and "PG" in levels_present:
        strength = "moderate"
    elif avg_score >= 50:
        strength = "fair"
    else:
        strength = "weak"

    # Step 9: Institution quality summary
    inst_quality_list = []
    for e in enriched:
        if e["education_level"] in ("UG", "PG", "PhD"):
            inst_quality_list.append({
                "degree": e["degree"],
                "institution": e["institution"],
                "quality": e["institution_quality"],
            })

    # Step 10: Generate interpretation
    interpretation_parts = []
    interpretation_parts.append(
        f"The candidate holds a {highest_qualification} "
        f"with {len(enriched)} recorded qualification(s)."
    )
    if progression_trend == "improving":
        interpretation_parts.append("Academic performance shows an improving trend.")
    elif progression_trend == "declining":
        interpretation_parts.append("Academic performance shows a declining trend, which may need attention.")
    else:
        interpretation_parts.append("Academic performance has been relatively stable.")

    if gaps:
        unjustified = [g for g in gaps if not g["justified"]]
        if unjustified:
            interpretation_parts.append(
                f"{len(unjustified)} unexplained educational gap(s) totaling "
                f"{sum(g['gap_years'] for g in unjustified)} year(s)."
            )
        else:
            interpretation_parts.append("All educational gaps are justified by professional activity.")
    else:
        interpretation_parts.append("No significant educational gaps detected.")

    # Add institution quality note
    tier1_insts = [i for i in inst_quality_list if i.get("quality", {}).get("tier") == 1]
    if tier1_insts:
        interpretation_parts.append(
            f"Attended {len(tier1_insts)} highly-ranked institution(s): "
            f"{', '.join(i['institution'] for i in tier1_insts)}."
        )
    elif inst_quality_list:
        interpretation_parts.append(
            "Institutions attended are recognized but not in top QS/THE rankings."
        )

    interpretation = " ".join(interpretation_parts)

    # Step 11: Build table for display
    table = []
    for e in enriched:
        table.append({
            "Level": e["education_level"],
            "Degree": e["degree"],
            "Specialization": e["specialization"],
            "Institution": e["institution"],
            "Score": e["original_score"],
            "Normalized (/100)": round(e["normalized_score"], 1) if e["normalized_score"] else "N/A",
            "Score Rating": e["score_interpretation"],
            "Year": e["year"],
            "Inst. Quality": e["institution_quality"].get("label", "N/A"),
        })

    summary = (
        f"{len(enriched)} education record(s). "
        f"Highest: {highest_qualification}. "
        f"Trend: {progression_trend}. Strength: {strength}."
    )

    return {
        "education_table": table,
        "education_levels": enriched,
        "degree_sequence": degree_sequence,
        "academic_pathway": pathway,
        "progression_trend": progression_trend,
        "highest_qualification": highest_qualification,
        "specialization_consistency": spec_consistency,
        "specialization_summary": spec_summary,
        "educational_gaps": gaps,
        "total_gap_years": total_gap_years,
        "academic_strength": strength,
        "interpretation": interpretation,
        "education_summary": summary,
        "institution_quality": inst_quality_list,
        "average_normalized_score": round(avg_score, 1) if scores else None,
        "progression_label": progression_trend,
    }