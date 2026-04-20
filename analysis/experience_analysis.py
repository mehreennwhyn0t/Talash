from datetime import datetime
import re


def parse_date(date_str):
    if not date_str:
        return None

    if isinstance(date_str, int):
        return datetime(date_str, 1, 1)

    try:
        return datetime.strptime(date_str.strip(), "%b-%Y")
    except:
        try:
            return datetime.strptime(date_str.strip(), "%Y")
        except:
            return None


def extract_dates_from_duration(duration):
    if not duration:
        return None, None

    parts = duration.split(" - ")

    if len(parts) == 2:
        start = parts[0].strip()
        end = parts[1].strip()

        return parse_date(start), parse_date(end)

    return None, None


def normalize_experience(experience_list):
    normalized = []

    for exp in experience_list:
        start = None
        end = None

        # Priority 1: duration field
        if exp.get("duration"):
            start, end = extract_dates_from_duration(exp["duration"])

        # Priority 2: fallback to year
        if not start and exp.get("start_year"):
            start = parse_date(exp["start_year"])

        if not end and exp.get("end_year"):
            end = parse_date(exp["end_year"])

        normalized.append({
            "title": exp.get("title", ""),
            "organization": exp.get("organization", ""),
            "start_date": start,
            "end_date": end,
            "raw": exp
        })

    return normalized

def detect_gaps(experiences):
    gaps = []

    sorted_exp = sorted(
        experiences,
        key=lambda x: x["start_date"] or datetime.min
    )

    for i in range(1, len(sorted_exp)):
        prev = sorted_exp[i - 1]
        curr = sorted_exp[i]

        if prev["end_date"] and curr["start_date"]:
            gap = (curr["start_date"] - prev["end_date"]).days

            if gap > 90:  # 3 months threshold
                gaps.append({
                    "between": (prev["organization"], curr["organization"]),
                    "gap_days": gap
                })

    return gaps


def detect_overlaps(experiences):
    overlaps = []

    for i in range(len(experiences)):
        for j in range(i + 1, len(experiences)):
            e1 = experiences[i]
            e2 = experiences[j]

            if e1["start_date"] and e2["start_date"]:
                if e1["end_date"] and e2["end_date"]:
                    if e1["start_date"] < e2["end_date"] and e2["start_date"] < e1["end_date"]:
                        overlaps.append((e1["organization"], e2["organization"]))

    return overlaps