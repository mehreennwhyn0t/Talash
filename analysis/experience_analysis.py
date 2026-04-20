from datetime import datetime
import re

def parse_date(date_str):
    if not date_str or date_str.lower() == "present":
        return None
    try:
        return datetime.strptime(date_str.strip(), "%b %Y")
    except:
        try:
            return datetime.strptime(date_str.strip(), "%Y")
        except:
            return None


def normalize_experience(experience_list):
    normalized = []

    for exp in experience_list:
        start = parse_date(exp.get("start_date", ""))
        end = parse_date(exp.get("end_date", ""))

        normalized.append({
            "title": exp.get("title", ""),
            "organization": exp.get("organization", ""),
            "start_date": start,
            "end_date": end,
            "raw": exp
        })

    return normalized