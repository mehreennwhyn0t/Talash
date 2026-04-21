from datetime import datetime
import re

ROLE_LEVELS = {
    "intern": 1, "trainee": 1,
    "junior": 2, "assistant": 2,
    "associate": 3, "lecturer": 3, "engineer": 3,
    "researcher": 3, "analyst": 3,
    "senior": 4, "manager": 4, "lead": 4,
    "assistant professor": 4,
    "associate professor": 5, "head": 5,
    "professor": 6, "director": 6,
    "dean": 7,
}


def parse_date(date_str):
    if not date_str:
        return None
    if isinstance(date_str, int):
        return datetime(date_str, 1, 1)
    date_str = str(date_str).strip()
    if date_str.lower() in ("present", "current", "now"):
        return datetime.now()
    for fmt in ("%b-%Y", "%B-%Y", "%Y"):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


def extract_dates_from_duration(duration):
    if not duration:
        return None, None
    # Split on " - " with spaces to avoid splitting "Feb-2014" on its own dash
    parts = duration.split(" - ", 1)
    if len(parts) == 2:
        return parse_date(parts[0].strip()), parse_date(parts[1].strip())
    return None, None


def normalize_experience(experience_list):
    normalized = []
    for exp in experience_list:
        start, end = None, None
        if exp.get("duration"):
            start, end = extract_dates_from_duration(exp["duration"])
        if not start and exp.get("start_year"):
            start = parse_date(str(exp["start_year"]))
        if not end and exp.get("end_year"):
            end = parse_date(str(exp["end_year"]))
        normalized.append({
            "title":        exp.get("title", ""),
            "organization": exp.get("organization", ""),
            "start_date":   start,
            "end_date":     end,
            "is_current":   end and end.year >= datetime.now().year,
            "raw":          exp
        })
    normalized.sort(key=lambda x: x["start_date"] or datetime.min)
    return normalized


def detect_gaps(experiences):
    gaps = []
    dated = [e for e in experiences if e["start_date"] and e["end_date"]]
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
                "after_role":   prev["title"],
                "after_org":    prev["organization"],
                "before_role":  curr["title"],
                "before_org":   curr["organization"],
                "gap_days":     gap_days,
                "gap_months":   months,
                "gap_readable": f"{months} month(s)",
                "severity":     severity,
            })
    return gaps


def detect_overlaps(experiences):
    overlaps = []
    for i in range(len(experiences)):
        for j in range(i + 1, len(experiences)):
            e1, e2 = experiences[i], experiences[j]
            if e1["start_date"] and e1["end_date"] and e2["start_date"] and e2["end_date"]:
                if e1["start_date"] < e2["end_date"] and e2["start_date"] < e1["end_date"]:
                    overlap_days = (
                        min(e1["end_date"], e2["end_date"]) -
                        max(e1["start_date"], e2["start_date"])
                    ).days
                    overlaps.append({
                        "role_a":         e1["title"],
                        "org_a":          e1["organization"],
                        "role_b":         e2["title"],
                        "org_b":          e2["organization"],
                        "overlap_months": overlap_days // 30,
                        "note": (
                            "Minor transition overlap — likely acceptable"
                            if overlap_days // 30 <= 3
                            else "Concurrent roles — may need clarification"
                        )
                    })
    return overlaps


def analyze_progression(experiences):
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
        return "Single role — insufficient data for progression analysis"
    mid        = len(scores) // 2
    first_avg  = sum(scores[:mid]) / mid
    second_avg = sum(scores[mid:]) / len(scores[mid:])
    diff = second_avg - first_avg
    if diff >= 2:
        return "Strong upward progression"
    elif diff >= 0.5:
        return "Moderate upward progression"
    elif diff >= -0.5:
        return "Lateral — consistent level maintained"
    else:
        return "Downward movement detected — may need clarification"


def generate_experience_summary(experiences, gaps, overlaps, progression_label):
    if not experiences:
        return "No professional experience records detected."
    total_roles = len(experiences)
    sig_gaps    = [g for g in gaps if g["severity"] == "significant"]
    parts = [f"The candidate has {total_roles} recorded role(s). {progression_label}."]
    if sig_gaps:
        parts.append(f"{len(sig_gaps)} significant employment gap(s) require explanation.")
    elif gaps:
        parts.append(f"{len(gaps)} minor gap(s) noted — likely transition periods.")
    else:
        parts.append("No significant employment gaps detected.")
    if overlaps:
        parts.append(f"{len(overlaps)} instance(s) of overlapping roles detected.")
    return " ".join(parts)


def analyze_experience(parsed_profile):
    """Main entry point — Member 3 calls this."""
    experiences = normalize_experience(parsed_profile.get("experience", []))
    gaps        = detect_gaps(experiences)
    overlaps    = detect_overlaps(experiences)
    progression = analyze_progression(experiences)
    summary     = generate_experience_summary(experiences, gaps, overlaps, progression)

    def serialize(e):
        out = dict(e)
        for k in ("start_date", "end_date"):
            if out.get(k):
                out[k] = out[k].strftime("%b %Y")
        out.pop("raw", None)
        return out

    return {
        "ordered_timeline":         [serialize(e) for e in experiences],
        "employment_gaps":          gaps,
        "job_overlaps":             overlaps,
        "career_progression_label": progression,
        "continuity_summary":       summary,
    }