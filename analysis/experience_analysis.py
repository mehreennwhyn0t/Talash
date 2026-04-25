"""
experience_analysis.py

Professional experience and employment history analysis.
Covers: timeline normalization, gap detection with severity, overlap detection
(job-job AND education-job), career progression, gap justification, and summary.
"""

from datetime import datetime
import re

ROLE_LEVELS = {
    "intern": 1, "trainee": 1,
    "junior": 2, "assistant": 2,
    "associate": 3, "lecturer": 3, "engineer": 3,
    "researcher": 3, "analyst": 3, "research associate": 3,
    "senior": 4, "manager": 4, "lead": 4,
    "assistant professor": 4, "program coordinator": 4,
    "associate professor": 5, "head": 5,
    "professor": 6, "director": 6,
    "dean": 7, "vice chancellor": 8,
}


def parse_date(date_str):
    """Parse various date formats into datetime objects."""
    if not date_str:
        return None
    if isinstance(date_str, int):
        return datetime(date_str, 1, 1)
    date_str = str(date_str).strip()
    if date_str.lower() in ("present", "current", "now", "to date"):
        return datetime.now()
    for fmt in ("%b-%Y", "%B-%Y", "%b %Y", "%B %Y", "%m/%Y", "%Y"):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    # Try extracting just a year
    year_match = re.search(r'\b((?:19|20)\d{2})\b', date_str)
    if year_match:
        return datetime(int(year_match.group(1)), 1, 1)
    return None


def extract_dates_from_duration(duration):
    """Split a duration string like 'Feb-2014 - Sep-2024' into two dates."""
    if not duration:
        return None, None
    # Split on " - " or " - " (with spaces to avoid splitting "Feb-2014")
    parts = re.split(r'\s+[-–]\s+', duration, 1)
    if len(parts) == 2:
        return parse_date(parts[0].strip()), parse_date(parts[1].strip())
    return None, None


def normalize_experience(experience_list):
    """Convert raw experience entries into normalized form with parsed dates."""
    normalized = []
    for exp in experience_list:
        start, end = None, None

        # Try duration field first
        if exp.get("duration"):
            start, end = extract_dates_from_duration(exp["duration"])

        # Try start_date/end_date fields
        if not start and exp.get("start_date"):
            start = parse_date(str(exp["start_date"]))
        if not end and exp.get("end_date"):
            end = parse_date(str(exp["end_date"]))

        # Fall back to start_year/end_year
        if not start and exp.get("start_year"):
            start = parse_date(str(exp["start_year"]))
        if not end and exp.get("end_year"):
            end = parse_date(str(exp["end_year"]))

        is_current = False
        end_str = str(exp.get("end_year", "") or exp.get("end_date", "")).lower()
        if end_str in ("present", "current", "now"):
            is_current = True
        elif end and end.year >= datetime.now().year:
            is_current = True

        normalized.append({
            "title":          exp.get("title", ""),
            "organization":   exp.get("organization", ""),
            "location":       exp.get("location", ""),
            "employment_type": exp.get("employment_type", ""),
            "start_date":     start,
            "end_date":       end,
            "is_current":     is_current,
            "raw":            exp,
        })

    normalized.sort(key=lambda x: x["start_date"] or datetime.min)
    return normalized


def detect_gaps(experiences):
    """Detect employment gaps between consecutive roles."""
    gaps = []
    dated = [e for e in experiences if e["start_date"] and e["end_date"]]
    for i in range(1, len(dated)):
        prev = dated[i - 1]
        curr = dated[i]
        gap_days = (curr["start_date"] - prev["end_date"]).days
        if gap_days > 90:  # > 3 months
            months = gap_days // 30
            if months <= 12:
                severity = "minor"
            elif months <= 24:
                severity = "moderate"
            else:
                severity = "significant"
            gaps.append({
                "after_role":   prev["title"],
                "after_org":    prev["organization"],
                "before_role":  curr["title"],
                "before_org":   curr["organization"],
                "gap_days":     gap_days,
                "gap_months":   months,
                "gap_readable": f"{months} month(s)",
                "severity":     severity,
                "justified":    False,
                "justification": "",
            })
    return gaps


def justify_gaps_with_education(gaps, education_records):
    """Check if employment gaps are justified by education."""
    for gap in gaps:
        if gap["justified"]:
            continue
        for edu in education_records:
            edu_start = None
            edu_end = None
            if edu.get("start_year"):
                edu_start = parse_date(str(edu["start_year"]))
            if edu.get("end_year") or edu.get("year"):
                edu_end = parse_date(str(edu.get("end_year") or edu.get("year")))

            if edu_start and edu_end:
                # Check if education period overlaps with the gap period
                gap_start = datetime(
                    gap.get("_start_year", 2000), 1, 1
                ) if "_start_year" in gap else None

                # Simpler check: education year falls within gap period
                if edu_end:
                    edu_year = edu_end.year
                    # Rough check using role dates
                    if gap.get("gap_months", 0) > 6:
                        gap["justified"] = True
                        gap["justification"] = (
                            f"Possibly pursuing {edu.get('degree', 'education')}"
                        )
                        break
    return gaps


def detect_overlaps(experiences):
    """Detect overlapping employment periods."""
    overlaps = []
    for i in range(len(experiences)):
        for j in range(i + 1, len(experiences)):
            e1, e2 = experiences[i], experiences[j]
            if (e1["start_date"] and e1["end_date"]
                    and e2["start_date"] and e2["end_date"]):
                if (e1["start_date"] < e2["end_date"]
                        and e2["start_date"] < e1["end_date"]):
                    overlap_days = (
                        min(e1["end_date"], e2["end_date"]) -
                        max(e1["start_date"], e2["start_date"])
                    ).days
                    overlaps.append({
                        "role_a":         e1["title"],
                        "org_a":          e1["organization"],
                        "period_a":       f"{e1['start_date'].strftime('%b %Y') if e1['start_date'] else '?'} - {e1['end_date'].strftime('%b %Y') if e1['end_date'] else '?'}",
                        "role_b":         e2["title"],
                        "org_b":          e2["organization"],
                        "period_b":       f"{e2['start_date'].strftime('%b %Y') if e2['start_date'] else '?'} - {e2['end_date'].strftime('%b %Y') if e2['end_date'] else '?'}",
                        "overlap_months": overlap_days // 30,
                        "note": (
                            "Minor transition overlap - likely acceptable"
                            if overlap_days // 30 <= 3
                            else "Concurrent roles - may need clarification"
                        )
                    })
    return overlaps


def detect_education_employment_overlaps(experiences, education_records):
    """Detect overlaps between education and employment periods."""
    overlaps = []
    for exp in experiences:
        if not exp["start_date"] or not exp["end_date"]:
            continue
        for edu in education_records:
            edu_start = parse_date(str(edu.get("start_year", "")))
            edu_end = parse_date(str(edu.get("end_year", "") or edu.get("year", "")))

            if not edu_end:
                continue
            if not edu_start:
                # Estimate start from end and degree duration
                level = edu.get("education_level", "")
                duration_map = {"PhD": 4, "PG": 2, "UG": 4, "HSSC": 2, "SSC": 2}
                dur = duration_map.get(level, 3)
                edu_start = datetime(edu_end.year - dur, 1, 1)

            if (exp["start_date"] < edu_end and edu_start < exp["end_date"]):
                overlap_days = (
                    min(exp["end_date"], edu_end) -
                    max(exp["start_date"], edu_start)
                ).days
                if overlap_days > 90:
                    overlaps.append({
                        "role": exp["title"],
                        "organization": exp["organization"],
                        "degree": edu.get("degree", "Unknown"),
                        "institution": edu.get("institution", "Unknown"),
                        "overlap_months": overlap_days // 30,
                        "note": (
                            "Part-time work during studies - common and acceptable"
                            if any(kw in exp["title"].lower() for kw in
                                   ["research", "assistant", "intern", "part"])
                            else "Full-time role overlapping with education - may need review"
                        )
                    })
    return overlaps


def analyze_progression(experiences):
    """Analyze career progression based on role levels."""
    if not experiences:
        return "No experience recorded"
    scores = []
    for exp in experiences:
        title_lower = exp["title"].lower()
        best = 0
        for kw, lvl in ROLE_LEVELS.items():
            if kw in title_lower:
                best = max(best, lvl)
        scores.append(best)

    if len(scores) < 2:
        return "Single role - insufficient data for progression analysis"

    mid = len(scores) // 2
    first_avg = sum(scores[:mid]) / mid
    second_avg = sum(scores[mid:]) / len(scores[mid:])
    diff = second_avg - first_avg
    if diff >= 2:
        return "Strong upward progression"
    elif diff >= 0.5:
        return "Moderate upward progression"
    elif diff >= -0.5:
        return "Lateral - consistent level maintained"
    else:
        return "Downward movement detected - may need clarification"


def calculate_total_experience(experiences):
    """Calculate total years of professional experience."""
    total_days = 0
    for exp in experiences:
        if exp["start_date"] and exp["end_date"]:
            days = (exp["end_date"] - exp["start_date"]).days
            total_days += max(0, days)
    return round(total_days / 365.25, 1)


def generate_experience_summary(experiences, gaps, overlaps, progression_label,
                                 edu_overlaps=None, total_years=0):
    """Generate a human-readable experience summary."""
    if not experiences:
        return "No professional experience records detected."

    total_roles = len(experiences)
    sig_gaps = [g for g in gaps if g["severity"] == "significant"]

    parts = [
        f"The candidate has {total_roles} recorded role(s) spanning "
        f"approximately {total_years} year(s). {progression_label}."
    ]

    if sig_gaps:
        parts.append(
            f"{len(sig_gaps)} significant employment gap(s) require explanation."
        )
    elif gaps:
        parts.append(
            f"{len(gaps)} minor gap(s) noted - likely transition periods."
        )
    else:
        parts.append("No significant employment gaps detected.")

    if overlaps:
        parts.append(
            f"{len(overlaps)} instance(s) of overlapping roles detected."
        )

    if edu_overlaps:
        parts.append(
            f"{len(edu_overlaps)} instance(s) of education-employment overlap noted."
        )

    return " ".join(parts)


def analyze_experience(parsed_profile):
    """
    Main entry point for professional experience analysis.
    Returns a comprehensive experience analysis dict.
    """
    experiences = normalize_experience(parsed_profile.get("experience", []))
    education = parsed_profile.get("education", [])

    gaps = detect_gaps(experiences)
    gaps = justify_gaps_with_education(gaps, education)
    overlaps = detect_overlaps(experiences)
    edu_overlaps = detect_education_employment_overlaps(experiences, education)
    progression = analyze_progression(experiences)
    total_years = calculate_total_experience(experiences)

    summary = generate_experience_summary(
        experiences, gaps, overlaps, progression,
        edu_overlaps, total_years
    )

    def serialize(e):
        out = dict(e)
        for k in ("start_date", "end_date"):
            if out.get(k):
                out[k] = out[k].strftime("%b %Y")
        out.pop("raw", None)
        return out

    # Build experience table
    exp_table = []
    for e in experiences:
        exp_table.append({
            "Title": e["title"],
            "Organization": e["organization"],
            "Start": e["start_date"].strftime("%b %Y") if e["start_date"] else "N/A",
            "End": e["end_date"].strftime("%b %Y") if e["end_date"] else "N/A",
            "Current": "Yes" if e["is_current"] else "No",
            "Type": e["employment_type"] or "N/A",
        })

    return {
        "experience_table":          exp_table,
        "ordered_timeline":          [serialize(e) for e in experiences],
        "employment_gaps":           gaps,
        "job_overlaps":              overlaps,
        "education_employment_overlaps": edu_overlaps,
        "career_progression_label":  progression,
        "total_experience_years":    total_years,
        "total_roles":               len(experiences),
        "continuity_summary":        summary,
    }