import re
import pandas as pd


def _safe_text(value):
    if value is None:
        return ""
    return str(value)


def _extract_first_number_near_keyword(text, keywords):
    text_lower = text.lower()

    for keyword in keywords:
        keyword_lower = keyword.lower()
        pattern_1 = rf"{keyword_lower}\D{{0,20}}(\d+)"
        pattern_2 = rf"(\d+)\D{{0,20}}{keyword_lower}"

        match = re.search(pattern_1, text_lower)
        if match:
            return int(match.group(1))

        match = re.search(pattern_2, text_lower)
        if match:
            return int(match.group(1))

    return 0


def _extract_isbn(text):
    match = re.search(r"(ISBN[:\s-]*[0-9Xx\- ]{10,20})", text, re.IGNORECASE)
    return match.group(1).strip() if match else "Missing"


def _extract_patent_number(text):
    match = re.search(r"(Patent\s*(Number|No\.?)[:\s-]*[A-Za-z0-9\-\/]+)", text, re.IGNORECASE)
    return match.group(1).strip() if match else "Missing"


def analyze_supervision_books_patents(parsed_data):
    """
    Analyze supervision, books, and patents from CV text.
    Input: parsed_data dictionary.
    Output: supervision table, books table, patents table, score, missing info, and summary.
    """

    if not isinstance(parsed_data, dict):
        parsed_data = {}

    text = (
        parsed_data.get("text", "")
        or parsed_data.get("raw_text", "")
        or parsed_data.get("cv_text", "")
        or ""
    )

    text = _safe_text(text)

    ms_count = _extract_first_number_near_keyword(
        text,
        ["MS supervised", "MPhil supervised", "master supervised", "masters supervised"]
    )

    phd_count = _extract_first_number_near_keyword(
        text,
        ["PhD supervised", "doctoral supervised"]
    )

    co_supervision_count = _extract_first_number_near_keyword(
        text,
        ["co-supervised", "co supervised", "co-supervision"]
    )

    book_count = len(re.findall(r"\bbook\b|\bbooks\b|book chapter", text, re.IGNORECASE))
    patent_count = len(re.findall(r"\bpatent\b|\binventor\b", text, re.IGNORECASE))

    supervision_table = pd.DataFrame([
        {"Type": "MS/MPhil Supervision", "Count": ms_count, "Role": "Main/Unknown"},
        {"Type": "PhD Supervision", "Count": phd_count, "Role": "Main/Unknown"},
        {"Type": "Co-supervision", "Count": co_supervision_count, "Role": "Co-supervisor"},
    ])

    books_table = pd.DataFrame([{
        "Detected Books/Chapters": book_count,
        "ISBN": _extract_isbn(text),
        "Publisher": "Missing",
        "Verification Status": "Needs verification"
    }])

    patents_table = pd.DataFrame([{
        "Detected Patents": patent_count,
        "Patent Number": _extract_patent_number(text),
        "Country": "Missing",
        "Verification Status": "Needs verification"
    }])

    missing_info = []

    if book_count > 0 and _extract_isbn(text) == "Missing":
        missing_info.append("Book information found but ISBN is missing")

    if book_count > 0:
        missing_info.append("Book publisher/year should be verified")

    if patent_count > 0 and _extract_patent_number(text) == "Missing":
        missing_info.append("Patent information found but patent number is missing")

    if patent_count > 0:
        missing_info.append("Patent country/status should be verified")

    if ms_count == 0 and phd_count == 0 and co_supervision_count == 0:
        missing_info.append("No supervision information found")

    score = 0
    score += min(ms_count * 5, 25)
    score += min(phd_count * 10, 30)
    score += min(co_supervision_count * 5, 15)
    score += min(book_count * 10, 15)
    score += min(patent_count * 15, 15)

    score = min(score, 100)

    summary = (
        f"The candidate has {ms_count} MS/MPhil supervision record(s), "
        f"{phd_count} PhD supervision record(s), and {co_supervision_count} co-supervision record(s). "
        f"The CV text indicates {book_count} book/book chapter mention(s) and {patent_count} patent-related mention(s). "
        f"Supervision, books, and patents score is {score}/100."
    )

    return {
        "supervision_table": supervision_table,
        "books_table": books_table,
        "patents_table": patents_table,
        "score": score,
        "missing_info": missing_info,
        "summary": summary,
    }