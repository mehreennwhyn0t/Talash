import re
import pandas as pd


def _safe_text(value):
    if value is None:
        return ""
    return str(value)


def _safe_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def analyze_supervision_books_patents(parsed_data):
    """
    Analyze supervision, books, and patents from parsed profile.
    Input: parsed_data dictionary from parser.
    Output: supervision table, books table, patents table, score, missing info, summary.
    """
    if not isinstance(parsed_data, dict):
        parsed_data = {}

    missing_info = []

    # ── Supervision ──────────────────────────────────────────────────────────
    supervision_list = parsed_data.get("supervision", []) or []
    ms_count  = 0
    phd_count = 0
    co_count  = 0

    if isinstance(supervision_list, list) and supervision_list:
        for s in supervision_list:
            if isinstance(s, dict):
                level = str(s.get("level", "")).lower()
                role  = str(s.get("role",  "")).lower()
                if "phd" in level or "doctoral" in level:
                    if "co" in role:
                        co_count += 1
                    else:
                        phd_count += 1
                else:
                    if "co" in role:
                        co_count += 1
                    else:
                        ms_count += 1
    else:
        # Fallback: scan raw text
        raw = (parsed_data.get("raw_text") or parsed_data.get("cv_text") or
               parsed_data.get("text") or "")
        text = _safe_text(raw).lower()
        ms_count  = len(re.findall(r'\b(ms|mphil|master)\s+(student|thesis|supervised)', text))
        phd_count = len(re.findall(r'\bphd\s+(student|thesis|supervised)', text))
        co_count  = len(re.findall(r'\bco[\-\s]supervis', text))

    if ms_count == 0 and phd_count == 0 and co_count == 0:
        missing_info.append("No supervision records detected — candidate may not have supervised students yet")

    supervision_table = pd.DataFrame([
        {"Type": "MS / MPhil Supervision",  "Count": ms_count,  "Role": "Main Supervisor"},
        {"Type": "PhD Supervision",          "Count": phd_count, "Role": "Main Supervisor"},
        {"Type": "Co-supervision (MS/PhD)",  "Count": co_count,  "Role": "Co-Supervisor"},
    ])

    # ── Books ────────────────────────────────────────────────────────────────
    books_list = parsed_data.get("books", []) or []
    book_rows  = []

    if isinstance(books_list, list) and books_list:
        for b in books_list:
            if isinstance(b, dict):
                book_rows.append({
                    "Title":      b.get("title", "Unknown"),
                    "Authors":    b.get("authors", "Unknown"),
                    "ISBN":       b.get("isbn", "Missing"),
                    "Publisher":  b.get("publisher", "Missing"),
                    "Year":       b.get("year", "Missing"),
                    "Link":       b.get("link", ""),
                    "Verification Status": "Needs verification" if not b.get("isbn") else "ISBN present",
                })
            if not b.get("isbn"):
                missing_info.append(f"Book ISBN missing: {b.get('title', 'Unknown title')[:50]}")
    else:
        book_rows.append({
            "Title": "None detected", "Authors": "", "ISBN": "N/A",
            "Publisher": "N/A", "Year": "N/A", "Link": "",
            "Verification Status": "No books found in CV",
        })
        missing_info.append("No books or book chapters detected in CV")

    books_table = pd.DataFrame(book_rows)

    # ── Patents ──────────────────────────────────────────────────────────────
    patents_list = parsed_data.get("patents", []) or []
    patent_rows  = []

    if isinstance(patents_list, list) and patents_list:
        for p in patents_list:
            if isinstance(p, dict):
                patent_rows.append({
                    "Patent Number": p.get("patent_number", "Missing"),
                    "Title":         p.get("title", "Unknown"),
                    "Date":          p.get("date", "Missing"),
                    "Inventors":     p.get("inventors", "Missing"),
                    "Country":       p.get("country", "Missing"),
                    "Link":          p.get("link", ""),
                    "Verification":  "Needs verification",
                })
            if not p.get("patent_number"):
                missing_info.append(f"Patent number missing: {p.get('title', 'Unknown')[:50]}")
    else:
        patent_rows.append({
            "Patent Number": "None detected", "Title": "", "Date": "",
            "Inventors": "", "Country": "", "Link": "",
            "Verification": "No patents found in CV",
        })

    patents_table = pd.DataFrame(patent_rows)

    # ── Score ────────────────────────────────────────────────────────────────
    score = 0
    score += min(ms_count  * 5,  25)
    score += min(phd_count * 10, 30)
    score += min(co_count  * 5,  15)
    book_count   = max(0, len(books_list)   if books_list   else 0)
    patent_count = max(0, len(patents_list) if patents_list else 0)
    score += min(book_count   * 10, 15)
    score += min(patent_count * 15, 15)
    score = min(score, 100)

    summary = (
        f"The candidate has {ms_count} MS/MPhil supervision(s), "
        f"{phd_count} PhD supervision(s), and {co_count} co-supervision(s). "
        f"{book_count} book/book chapter(s) and {patent_count} patent(s) detected. "
        f"Supervision, books, and patents score: {score}/100."
    )

    return {
        "supervision_table": supervision_table,
        "books_table":       books_table,
        "patents_table":     patents_table,
        "ms_count":          ms_count,
        "phd_count":         phd_count,
        "co_count":          co_count,
        "book_count":        book_count,
        "patent_count":      patent_count,
        "score":             score,
        "missing_info":      missing_info,
        "summary":           summary,
    }


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