"""
experience_analysis.py

Professional experience and employment history analysis.
Milestone 3 version.

Covers:
- Timeline normalization
- Total experience calculation
- Employment gap detection
- Job-job overlap detection
- Education-employment overlap detection
- Career progression analysis
- Experience score out of 100
- Human-readable summary
"""

from datetime import datetime
import re


ROLE_LEVELS = {
    "intern": 1,
    "trainee": 1,
    "junior": 2,
    "teaching assistant": 2,
    "research assistant": 2,
    "assistant": 2,
    "associate": 3,
    "lecturer": 3,
    "engineer": 3,
    "developer": 3,
    "researcher": 3,
    "analyst": 3,
    "research associate": 3,
    "software engineer": 3,
    "senior": 4,
    "manager": 4,
    "lead": 4,
    "assistant professor": 4,
    "program coordinator": 4,
    "associate professor": 5,
    "head": 5,
    "principal": 5,
    "professor": 6,
    "director": 6,
    "dean": 7,
    "vice chancellor": 8,
}


def parse_date(date_str):
    """Parse different date formats into datetime objects."""
    if not date_str:
        return None

    if isinstance(date_str, int):
        return datetime(date_str, 1, 1)

    date_str = str(date_str).strip()

    if not date_str:
        return None

    lowered = date_str.lower()

    if lowered in ("present", "current", "now", "to date", "till date", "ongoing"):
        return datetime.now()

    date_str = date_str.replace("/", "-").replace(".", "-")

    for fmt in (
        "%b-%Y",
        "%B-%Y",
        "%b %Y",
        "%B %Y",
        "%m-%Y",
        "%Y-%m",
        "%Y",
    ):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue

    year_match = re.search(r"\b((?:19|20)\d{2})\b", date_str)
    if year_match:
        return datetime(int(year_match.group(1)), 1, 1)

    return None


def extract_dates_from_duration(duration):
    """
    Split duration strings like:
    'Feb-2014 - Sep-2024'
    'Jan 2020 - Present'
    '2018 to 2021'
    """
    if not duration:
        return None, None

    duration = str(duration).strip()

    patterns = [
        r"(.+?)\s+[-–—]\s+(.+)",
        r"(.+?)\s+to\s+(.+)",
        r"(.+?)\s+TO\s+(.+)",
    ]

    for pattern in patterns:
        match = re.match(pattern, duration)
        if match:
            start_text = match.group(1).strip()
            end_text = match.group(2).strip()
            return parse_date(start_text), parse_date(end_text)

    years = re.findall(r"\b((?:19|20)\d{2})\b", duration)

    if len(years) >= 2:
        return parse_date(years[0]), parse_date(years[1])

    if len(years) == 1:
        return parse_date(years[0]), None

    return None, None


def normalize_experience(experience_list):
    """Convert raw experience entries into normalized form with parsed dates."""
    normalized = []

    for exp in experience_list or []:
        if not isinstance(exp, dict):
            continue

        start, end = None, None

        duration = exp.get("duration") or exp.get("period") or ""

        if duration:
            start, end = extract_dates_from_duration(duration)

        if not start:
            start = (
                parse_date(exp.get("start_date"))
                or parse_date(exp.get("start_year"))
                or parse_date(exp.get("from"))
            )

        if not end:
            end = (
                parse_date(exp.get("end_date"))
                or parse_date(exp.get("end_year"))
                or parse_date(exp.get("to"))
            )

        is_current = False
        end_text = str(
            exp.get("end_year")
            or exp.get("end_date")
            or exp.get("to")
            or duration
            or ""
        ).lower()

        if any(word in end_text for word in ["present", "current", "now", "to date", "ongoing"]):
            is_current = True
            if not end:
                end = datetime.now()

        title = (
            exp.get("title")
            or exp.get("job_title")
            or exp.get("position")
            or exp.get("designation")
            or ""
        )

        organization = (
            exp.get("organization")
            or exp.get("org")
            or exp.get("company")
            or exp.get("institution")
            or ""
        )

        normalized.append({
            "title": str(title).strip(),
            "organization": str(organization).strip(),
            "location": exp.get("location", ""),
            "employment_type": exp.get("employment_type", ""),
            "duration": duration,
            "start_date": start,
            "end_date": end,
            "is_current": is_current,
            "raw": exp,
        })

    normalized.sort(key=lambda x: x["start_date"] or datetime.min)
    return normalized


def role_level(title):
    """Return numeric role seniority level."""
    title_lower = str(title).lower()
    best = 0

    for keyword, level in ROLE_LEVELS.items():
        if keyword in title_lower:
            best = max(best, level)

    return best or 2


def detect_gaps(experiences):
    """Detect employment gaps between consecutive roles."""
    gaps = []
    dated = [e for e in experiences if e["start_date"] and e["end_date"]]
    dated.sort(key=lambda x: x["start_date"])

    for i in range(1, len(dated)):
        prev = dated[i - 1]
        curr = dated[i]

        gap_days = (curr["start_date"] - prev["end_date"]).days

        if gap_days > 90:
            months = gap_days // 30

            if months <= 12:
                severity = "minor"
            elif months <= 24:
                severity = "moderate"
            else:
                severity = "significant"

            gaps.append({
                "after_role": prev["title"],
                "after_org": prev["organization"],
                "before_role": curr["title"],
                "before_org": curr["organization"],
                "gap_days": gap_days,
                "gap_months": months,
                "gap_readable": f"{months} month(s)",
                "severity": severity,
                "justified": False,
                "justification": "",
                "_gap_start": prev["end_date"],
                "_gap_end": curr["start_date"],
            })

    return gaps


def justify_gaps_with_education(gaps, education_records):
    """Check whether employment gaps overlap with education period."""
    for gap in gaps:
        gap_start = gap.get("_gap_start")
        gap_end = gap.get("_gap_end")

        if not gap_start or not gap_end:
            continue

        for edu in education_records or []:
            if not isinstance(edu, dict):
                continue

            edu_start = parse_date(
                edu.get("start_year")
                or edu.get("start_date")
                or edu.get("admission_year")
            )

            edu_end = parse_date(
                edu.get("end_year")
                or edu.get("end_date")
                or edu.get("year")
                or edu.get("passing_year")
                or edu.get("completion_year")
            )

            if not edu_end:
                continue

            if not edu_start:
                level = str(edu.get("education_level", "")).upper()
                degree = str(edu.get("degree", "")).lower()

                if "phd" in degree or level == "PHD":
                    edu_start = datetime(edu_end.year - 4, 1, 1)
                elif "ms" in degree or "mphil" in degree or level == "PG":
                    edu_start = datetime(edu_end.year - 2, 1, 1)
                elif "bs" in degree or "bsc" in degree or level == "UG":
                    edu_start = datetime(edu_end.year - 4, 1, 1)
                else:
                    edu_start = datetime(edu_end.year - 2, 1, 1)

            overlap_start = max(gap_start, edu_start)
            overlap_end = min(gap_end, edu_end)

            if overlap_start < overlap_end:
                gap["justified"] = True
                gap["justification"] = f"Possibly justified by {edu.get('degree', 'education')}"
                break

    for gap in gaps:
        gap.pop("_gap_start", None)
        gap.pop("_gap_end", None)

    return gaps


def detect_overlaps(experiences):
    """Detect overlapping employment periods."""
    overlaps = []

    for i in range(len(experiences)):
        for j in range(i + 1, len(experiences)):
            e1 = experiences[i]
            e2 = experiences[j]

            if not all([e1["start_date"], e1["end_date"], e2["start_date"], e2["end_date"]]):
                continue

            if e1["start_date"] < e2["end_date"] and e2["start_date"] < e1["end_date"]:
                overlap_days = (
                    min(e1["end_date"], e2["end_date"])
                    - max(e1["start_date"], e2["start_date"])
                ).days

                overlap_months = max(0, overlap_days // 30)

                overlaps.append({
                    "role_a": e1["title"],
                    "org_a": e1["organization"],
                    "period_a": f"{e1['start_date'].strftime('%b %Y')} - {e1['end_date'].strftime('%b %Y')}",
                    "role_b": e2["title"],
                    "org_b": e2["organization"],
                    "period_b": f"{e2['start_date'].strftime('%b %Y')} - {e2['end_date'].strftime('%b %Y')}",
                    "overlap_months": overlap_months,
                    "note": (
                        "Minor transition overlap - likely acceptable"
                        if overlap_months <= 3
                        else "Concurrent roles - may need clarification"
                    ),
                })

    return overlaps


def detect_education_employment_overlaps(experiences, education_records):
    """Detect overlaps between education and employment periods."""
    overlaps = []

    for exp in experiences:
        if not exp["start_date"] or not exp["end_date"]:
            continue

        for edu in education_records or []:
            if not isinstance(edu, dict):
                continue

            edu_start = parse_date(
                edu.get("start_year")
                or edu.get("start_date")
                or edu.get("admission_year")
            )

            edu_end = parse_date(
                edu.get("end_year")
                or edu.get("end_date")
                or edu.get("year")
                or edu.get("passing_year")
                or edu.get("completion_year")
            )

            if not edu_end:
                continue

            if not edu_start:
                degree = str(edu.get("degree", "")).lower()
                level = str(edu.get("education_level", "")).upper()

                if "phd" in degree or level == "PHD":
                    edu_start = datetime(edu_end.year - 4, 1, 1)
                elif "ms" in degree or "mphil" in degree or level == "PG":
                    edu_start = datetime(edu_end.year - 2, 1, 1)
                elif "bs" in degree or "bsc" in degree or level == "UG":
                    edu_start = datetime(edu_end.year - 4, 1, 1)
                else:
                    edu_start = datetime(edu_end.year - 2, 1, 1)

            if exp["start_date"] < edu_end and edu_start < exp["end_date"]:
                overlap_days = (
                    min(exp["end_date"], edu_end)
                    - max(exp["start_date"], edu_start)
                ).days

                if overlap_days > 90:
                    overlap_months = overlap_days // 30

                    title_lower = exp["title"].lower()
                    acceptable_keywords = ["research", "assistant", "intern", "part", "lecturer", "teaching"]

                    overlaps.append({
                        "role": exp["title"],
                        "organization": exp["organization"],
                        "degree": edu.get("degree", "Unknown"),
                        "institution": edu.get("institution", "Unknown"),
                        "overlap_months": overlap_months,
                        "note": (
                            "May be acceptable if role was part-time, teaching, research, or flexible"
                            if any(kw in title_lower for kw in acceptable_keywords)
                            else "Full-time role overlapping with education - may need review"
                        ),
                    })

    return overlaps


def analyze_progression(experiences):
    """Analyze career progression based on role levels."""
    if not experiences:
        return "No experience recorded"

    scores = [role_level(exp["title"]) for exp in experiences]

    if len(scores) < 2:
        return "Single role - insufficient data for progression analysis"

    mid = len(scores) // 2
    first_half = scores[:mid]
    second_half = scores[mid:]

    first_avg = sum(first_half) / max(1, len(first_half))
    second_avg = sum(second_half) / max(1, len(second_half))

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


def calculate_experience_score(total_years, gaps, overlaps, progression_label):
    """Calculate experience score out of 100."""
    score = 0

    if total_years >= 10:
        score += 35
    elif total_years >= 5:
        score += 28
    elif total_years >= 2:
        score += 20
    elif total_years > 0:
        score += 10

    if "Strong upward" in progression_label:
        score += 25
    elif "Moderate upward" in progression_label:
        score += 20
    elif "Lateral" in progression_label:
        score += 12
    elif "Single role" in progression_label:
        score += 8

    serious_gaps = [g for g in gaps if g.get("severity") in ["moderate", "significant"] and not g.get("justified")]

    if not serious_gaps:
        score += 20
    elif len(serious_gaps) == 1:
        score += 12
    else:
        score += 5

    serious_overlaps = [
        o for o in overlaps
        if "clarification" in o.get("note", "").lower()
    ]

    if not serious_overlaps:
        score += 20
    else:
        score += 8

    return min(100, score)


def get_experience_strength(score):
    if score >= 80:
        return "Strong Professional Profile"
    if score >= 60:
        return "Good Professional Profile"
    if score >= 40:
        return "Needs Review"
    return "Weak or Insufficient Experience Data"


def generate_experience_summary(
    experiences,
    gaps,
    overlaps,
    progression_label,
    edu_overlaps=None,
    total_years=0,
    experience_score=0,
    experience_strength="",
):
    """Generate a human-readable experience summary."""
    if not experiences:
        return "No professional experience records detected."

    total_roles = len(experiences)
    significant_gaps = [g for g in gaps if g.get("severity") == "significant"]

    parts = [
        f"The candidate has {total_roles} recorded role(s) spanning approximately {total_years} year(s).",
        f"Career progression: {progression_label}.",
        f"Experience score: {experience_score}/100 ({experience_strength}).",
    ]

    if significant_gaps:
        parts.append(f"{len(significant_gaps)} significant employment gap(s) require explanation.")
    elif gaps:
        parts.append(f"{len(gaps)} minor/moderate gap(s) noted.")
    else:
        parts.append("No significant employment gaps detected.")

    if overlaps:
        parts.append(f"{len(overlaps)} job-job overlap instance(s) detected.")

    if edu_overlaps:
        parts.append(f"{len(edu_overlaps)} education-employment overlap instance(s) noted.")

    return " ".join(parts)


def analyze_experience(parsed_profile):
    """
    Main entry point for professional experience analysis.
    Returns a comprehensive experience analysis dictionary.
    """
    experiences = normalize_experience(parsed_profile.get("experience", []))
    education = parsed_profile.get("education", [])

    gaps = detect_gaps(experiences)
    gaps = justify_gaps_with_education(gaps, education)

    overlaps = detect_overlaps(experiences)
    edu_overlaps = detect_education_employment_overlaps(experiences, education)

    progression = analyze_progression(experiences)
    total_years = calculate_total_experience(experiences)

    experience_score = calculate_experience_score(
        total_years,
        gaps,
        overlaps,
        progression,
    )

    experience_strength = get_experience_strength(experience_score)

    summary = generate_experience_summary(
        experiences,
        gaps,
        overlaps,
        progression,
        edu_overlaps,
        total_years,
        experience_score,
        experience_strength,
    )

    def serialize(e):
        out = dict(e)
        for key in ("start_date", "end_date"):
            if out.get(key):
                out[key] = out[key].strftime("%b %Y")
        out.pop("raw", None)
        return out

    exp_table = []

    for e in experiences:
        exp_table.append({
            "Title": e["title"],
            "Organization": e["organization"],
            "Start": e["start_date"].strftime("%b %Y") if e["start_date"] else "N/A",
            "End": e["end_date"].strftime("%b %Y") if e["end_date"] else "N/A",
            "Current": "Yes" if e["is_current"] else "No",
            "Type": e["employment_type"] or "N/A",
            "Seniority Score": role_level(e["title"]),
        })

    return {
        "experience_table": exp_table,
        "ordered_timeline": [serialize(e) for e in experiences],
        "timeline": [serialize(e) for e in experiences],

        "employment_gaps": gaps,
        "job_overlaps": overlaps,
        "education_employment_overlaps": edu_overlaps,

        "career_progression_label": progression,
        "career_progression": progression,

        "total_experience_years": total_years,
        "total_roles": len(experiences),

        "experience_score": experience_score,
        "experience_strength": experience_strength,

        "continuity_summary": summary,
        "summary": summary,
    }


def get_experience_score(parsed_profile):
    return analyze_experience(parsed_profile).get("experience_score", 0)