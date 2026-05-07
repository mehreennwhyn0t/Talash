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
    Comprehensive Milestone 3 analysis of supervision, books, and patents.
    Prioritizes structured data from LLM but falls back to regex-based raw text scanning.
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
    missing_info = []

    # ── Supervision ──────────────────────────────────────────────────────────
    supervision_list = parsed_data.get("supervision", []) or []
    ms_count  = 0
    phd_count = 0
    co_count  = 0

    if isinstance(supervision_list, list) and supervision_list:
        for s in supervision_list:
            if isinstance(s, dict):
                level = str(s.get("degree_level", s.get("level", ""))).lower()
                role  = str(s.get("role",  "")).lower()
                if "phd" in level or "doctoral" in level:
                    if "co" in role: co_count += 1
                    else: phd_count += 1
                else:
                    if "co" in role: co_count += 1
                    else: ms_count += 1
    
    # If counts are still 0, try regex scan from text
    if ms_count == 0 and phd_count == 0 and co_count == 0 and text:
        ms_count = _extract_first_number_near_keyword(
            text, ["MS supervised", "MPhil supervised", "master supervised", "masters supervised"]
        )
        if ms_count == 0:
            ms_count = len(re.findall(r'\b(ms|mphil|master)\s+(student|thesis|supervised)', text, re.I))
            
        phd_count = _extract_first_number_near_keyword(
            text, ["PhD supervised", "doctoral supervised"]
        )
        if phd_count == 0:
            phd_count = len(re.findall(r'\bphd\s+(student|thesis|supervised)', text, re.I))
            
        co_count = _extract_first_number_near_keyword(
            text, ["co-supervised", "co supervised", "co-supervision"]
        )
        if co_count == 0:
            co_count = len(re.findall(r'\bco[\-\s]supervis', text, re.I))

    supervision_table = pd.DataFrame([
        {"Type": "MS / MPhil Supervision",  "Count": ms_count,  "Role": "Main/Unknown"},
        {"Type": "PhD Supervision",          "Count": phd_count, "Role": "Main/Unknown"},
        {"Type": "Co-supervision",           "Count": co_count,  "Role": "Co-Supervisor"},
    ])

    # ── Books ────────────────────────────────────────────────────────────────
    books_list = parsed_data.get("books", []) or []
    book_rows  = []

    if isinstance(books_list, list) and books_list:
        for b in books_list:
            if isinstance(b, dict):
                book_rows.append({
                    "Title":      b.get("title", "Unknown"),
                    "Authors":    ", ".join(b.get("authors", [])) if isinstance(b.get("authors"), list) else b.get("authors", "Unknown"),
                    "ISBN":       b.get("isbn", "Missing"),
                    "Publisher":  b.get("publisher", "Missing"),
                    "Year":       b.get("year", "Missing"),
                    "Verification Status": "ISBN present" if b.get("isbn") and b.get("isbn") != "Missing" else "Needs verification",
                })
    
    # Fallback to text scan if no books found
    if not book_rows and text:
        reg_count = len(re.findall(r"\bbook\b|\bbooks\b|book chapter", text, re.IGNORECASE))
        if reg_count > 0:
            book_rows.append({
                "Title": f"Detected {reg_count} book mention(s) in CV",
                "Authors": "N/A",
                "ISBN": _extract_isbn(text),
                "Publisher": "Missing",
                "Year": "N/A",
                "Verification Status": "Needs manual verification"
            })

    if not book_rows:
        book_rows.append({
            "Title": "None detected", "Authors": "", "ISBN": "N/A",
            "Publisher": "N/A", "Year": "N/A", "Verification Status": "No books found",
        })
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
                    "Date":          p.get("date", p.get("year", "Missing")),
                    "Inventors":     ", ".join(p.get("inventors", [])) if isinstance(p.get("inventors"), list) else p.get("inventors", "Missing"),
                    "Country":       p.get("country", "Missing"),
                    "Verification":  "Patent number present" if p.get("patent_number") and p.get("patent_number") != "Missing" else "Needs verification",
                })

    if not patent_rows and text:
        reg_count = len(re.findall(r"\bpatent\b|\binventor\b", text, re.IGNORECASE))
        if reg_count > 0:
            patent_rows.append({
                "Patent Number": _extract_patent_number(text),
                "Title": f"Detected {reg_count} patent mention(s)",
                "Date": "N/A",
                "Inventors": "N/A",
                "Country": "N/A",
                "Verification": "Needs manual verification"
            })

    if not patent_rows:
        patent_rows.append({
            "Patent Number": "None detected", "Title": "", "Date": "",
            "Inventors": "", "Country": "", "Verification": "No patents found",
        })
    patents_table = pd.DataFrame(patent_rows)

    # ── Score ────────────────────────────────────────────────────────────────
    score = 0
    score += min(ms_count  * 5,  25)
    score += min(phd_count * 10, 30)
    score += min(co_count  * 5,  15)
    
    # Accurate count for scoring
    final_book_count = len(books_list) if books_list else (1 if "Detected" in book_rows[0]["Title"] else 0)
    final_patent_count = len(patents_list) if patents_list else (1 if "Detected" in patent_rows[0]["Patent Number"] else 0)
    
    score += min(final_book_count * 10, 15)
    score += min(final_patent_count * 15, 15)
    score = min(score, 100)

    # ── Missing Info ─────────────────────────────────────────────────────────
    if ms_count == 0 and phd_count == 0:
        missing_info.append("No student supervision records detected")
    if final_book_count > 0 and any(r.get("ISBN") == "Missing" for r in book_rows):
        missing_info.append("Book(s) detected but ISBN missing for verification")
    if final_patent_count > 0 and any(r.get("Patent Number") == "Missing" for r in patent_rows):
        missing_info.append("Patent(s) detected but patent number missing")

    summary = (
        f"The candidate has {ms_count} MS and {phd_count} PhD supervision(s). "
        f"{final_book_count} book(s) and {final_patent_count} patent(s) detected. "
        f"Overall Milestone 3 Supervision/IP score: {score}/100."
    )

    return {
        "supervision_table": supervision_table,
        "books_table":       books_table,
        "patents_table":     patents_table,
        "ms_count":          ms_count,
        "phd_count":         phd_count,
        "co_count":          co_count,
        "book_count":        final_book_count,
        "patent_count":      final_patent_count,
        "score":             score,
        "missing_info":      missing_info,
        "summary":           summary,
    }