import re
from typing import Optional


LEVEL_ORDER = {
    "SSC": 1,
    "HSSC": 2,
    "UG": 3,
    "PG": 4,
    "PhD": 5,
    "Unknown": 99,
}


def safe_int(value) -> Optional[int]:
    """
    Convert value to int if possible, else return None.
    """
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def classify_education_level(degree: str) -> str:
    """
    Classify education level from degree title.
    """
    if not degree:
        return "Unknown"

    degree_lower = degree.lower().strip()

    if "phd" in degree_lower or "doctor" in degree_lower:
        return "PhD"

    if (
        "ms" in degree_lower
        or "m.sc" in degree_lower
        or "msc" in degree_lower
        or "master" in degree_lower
        or "mphil" in degree_lower
        or "m.phil" in degree_lower
    ):
        return "PG"

    if (
        "bs" in degree_lower
        or "b.sc" in degree_lower
        or "bsc" in degree_lower
        or "be" in degree_lower
        or "b.e" in degree_lower
        or "bachelor" in degree_lower
    ):
        return "UG"

    if (
        "hssc" in degree_lower
        or "intermediate" in degree_lower
        or "fsc" in degree_lower
        or "f.sc" in degree_lower
        or "a-level" in degree_lower
    ):
        return "HSSC"

    if (
        "ssc" in degree_lower
        or "matric" in degree_lower
        or "o-level" in degree_lower
    ):
        return "SSC"

    return "Unknown"


def detect_score_type(score: str) -> str:
    """
    Detect whether a score looks like:
    - percentage
    - cgpa_4
    - cgpa_5
    - percentage_like
    - unknown
    """
    if not score:
        return "unknown"

    s = str(score).strip().lower()

    if "%" in s:
        return "percentage"

    cleaned = re.sub(r"[^\d.]", "", s)
    if not cleaned:
        return "unknown"

    try:
        value = float(cleaned)
    except ValueError:
        return "unknown"

    if value <= 4.0:
        return "cgpa_4"
    if value <= 5.0:
        return "cgpa_5"
    if value <= 100:
        return "percentage_like"

    return "unknown"


def normalize_score_to_100(score: str) -> Optional[float]:
    """
    Normalize score to a /100 scale when possible.
    Returns None when normalization is not possible.
    """
    if not score:
        return None

    cleaned = re.sub(r"[^\d.]", "", str(score))
    if not cleaned:
        return None

    try:
        value = float(cleaned)
    except ValueError:
        return None

    score_type = detect_score_type(score)

    if score_type in {"percentage", "percentage_like"}:
        return round(value, 2)

    if score_type == "cgpa_4":
        return round((value / 4.0) * 100, 2)

    if score_type == "cgpa_5":
        return round((value / 5.0) * 100, 2)

    return None


def extract_specialization_from_degree(degree: str) -> str:
    """
    Lightweight heuristic to extract specialization from degree text.
    Keeps this simple for Milestone 2.
    """
    if not degree:
        return ""

    degree_clean = " ".join(str(degree).split())

    splitters = [" in ", " - ", " (", " Engineering ", " Sciences "]
    for splitter in splitters:
        if splitter.lower() in degree_clean.lower():
            parts = re.split(splitter, degree_clean, maxsplit=1, flags=re.IGNORECASE)
            if len(parts) > 1:
                return parts[1].strip(" )-,")

    return ""


def sort_education_key(record: dict):
    """
    Sorting helper:
    1. by education level
    2. by year
    """
    level = record.get("education_level", "Unknown")
    year_int = record.get("year_int")

    return (
        LEVEL_ORDER.get(level, 99),
        year_int if year_int is not None else 9999,
    )