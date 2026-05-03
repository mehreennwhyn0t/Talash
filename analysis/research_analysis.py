import os
import re
import pandas as pd


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JOURNAL_LOOKUP_PATH = os.path.join(BASE_DIR, "data", "lookup", "journal_rankings.csv")
CONFERENCE_LOOKUP_PATH = os.path.join(BASE_DIR, "data", "lookup", "conference_rankings.csv")


def _safe_text(value):
    if value is None:
        return ""
    return str(value).strip()


def _load_lookup(path):
    if os.path.exists(path):
        return pd.read_csv(path)
    return pd.DataFrame()


def _find_lookup_match(venue, lookup_df):
    if lookup_df.empty or not venue:
        return None

    venue_lower = venue.lower().strip()

    for _, row in lookup_df.iterrows():
        lookup_venue = str(row.get("venue", "")).lower().strip()
        if lookup_venue and (lookup_venue in venue_lower or venue_lower in lookup_venue):
            return row

    return None


def _detect_publication_type(text, venue):
    combined = f"{text} {venue}".lower()

    if any(word in combined for word in ["conference", "proceedings", "symposium", "workshop"]):
        return "Conference"

    if any(word in combined for word in ["journal", "ieee access", "plos", "springer", "elsevier"]):
        return "Journal"

    return "Unknown"


def _extract_year(text):
    match = re.search(r"(19|20)\d{2}", text)
    return match.group(0) if match else "Unknown"


def _detect_role(authors, candidate_name=""):
    authors_text = _safe_text(authors)
    candidate = _safe_text(candidate_name)

    if not authors_text:
        return "Unknown"

    author_list = [a.strip() for a in re.split(r",|;|\band\b", authors_text) if a.strip()]

    if not candidate:
        return "Co-author" if len(author_list) > 1 else "Single Author"

    candidate_lower = candidate.lower()

    for idx, author in enumerate(author_list):
        if candidate_lower in author.lower() or author.lower() in candidate_lower:
            if len(author_list) == 1:
                return "Single Author"
            if idx == 0:
                return "First Author"
            return "Co-author"

    return "Unknown"


def _extract_publications_from_text(text):
    text = _safe_text(text)
    publications = []

    lines = [line.strip() for line in text.splitlines() if line.strip()]

    for line in lines:
        lower = line.lower()

        publication_keywords = [
            "journal",
            "conference",
            "publication",
            "published",
            "paper",
            "proceedings",
            "ieee",
            "springer",
            "elsevier",
            "plos",
        ]

        if any(keyword in lower for keyword in publication_keywords):
            title = line
            venue = "Unknown"

            known_venues = [
                "IEEE Access",
                "PLOS ONE",
                "Springer Nature",
                "Elsevier Journal",
                "IEEE Conference",
                "ACM Conference",
                "Springer Conference",
                "NeurIPS",
                "ICML",
                "ACL",
            ]

            for known in known_venues:
                if known.lower() in lower:
                    venue = known
                    break

            publications.append({
                "title": title,
                "year": _extract_year(line),
                "venue": venue,
                "authors": "",
                "raw_text": line
            })

    return publications


def _get_publications(parsed_data):
    if not isinstance(parsed_data, dict):
        return []

    publications = parsed_data.get("publications", [])

    if isinstance(publications, list) and publications:
        return publications

    text = parsed_data.get("text", "") or parsed_data.get("raw_text", "") or parsed_data.get("cv_text", "")
    return _extract_publications_from_text(text)


def analyze_research_profile(parsed_data):
    """
    Main function for Huma's Milestone 3 research profile analysis.
    Input: parsed_data dictionary from parser.
    Output: dictionary with table, counts, score, missing info, and summary.
    """

    journal_lookup = _load_lookup(JOURNAL_LOOKUP_PATH)
    conference_lookup = _load_lookup(CONFERENCE_LOOKUP_PATH)

    candidate_name = ""
    if isinstance(parsed_data, dict):
        candidate_name = parsed_data.get("name", "") or parsed_data.get("candidate_name", "")

    publications = _get_publications(parsed_data)

    rows = []
    missing_info = []

    for idx, pub in enumerate(publications, start=1):
        if isinstance(pub, dict):
            title = _safe_text(pub.get("title", ""))
            year = _safe_text(pub.get("year", ""))
            venue = _safe_text(pub.get("venue", ""))
            authors = _safe_text(pub.get("authors", ""))
            raw_text = _safe_text(pub.get("raw_text", title))
        else:
            title = _safe_text(pub)
            year = _extract_year(title)
            venue = "Unknown"
            authors = ""
            raw_text = title

        if not title:
            title = f"Publication {idx}"
            missing_info.append(f"Publication {idx}: missing title")

        if not year:
            year = _extract_year(raw_text)

        if not year or year == "Unknown":
            missing_info.append(f"{title}: missing publication year")

        if not venue:
            venue = "Unknown"
            missing_info.append(f"{title}: missing venue name")

        pub_type = _detect_publication_type(raw_text, venue)

        indexing = "Unknown"
        quartile_or_rank = "Unknown"
        impact_factor = ""
        quality_score = 30

        if pub_type == "Journal":
            match = _find_lookup_match(venue, journal_lookup)
            if match is not None:
                indexing = match.get("indexing", "Unknown")
                quartile_or_rank = match.get("quartile", "Unknown")
                impact_factor = match.get("impact_factor", "")
                quality_score = int(match.get("score", 30))
            else:
                missing_info.append(f"{title}: journal not found in ranking lookup")

        elif pub_type == "Conference":
            match = _find_lookup_match(venue, conference_lookup)
            if match is not None:
                indexing = match.get("indexing", "Unknown")
                quartile_or_rank = match.get("core_rank", "Unknown")
                quality_score = int(match.get("score", 30))
            else:
                missing_info.append(f"{title}: conference not found in ranking lookup")

        else:
            missing_info.append(f"{title}: publication type is unclear")

        role = _detect_role(authors, candidate_name)

        if not authors:
            missing_info.append(f"{title}: missing authors list")

        rows.append({
            "Title": title,
            "Year": year if year else "Unknown",
            "Type": pub_type,
            "Venue": venue if venue else "Unknown",
            "Authors": authors if authors else "Unknown",
            "Candidate Role": role,
            "Indexing": indexing,
            "Quartile/Rank": quartile_or_rank,
            "Impact Factor": impact_factor,
            "Quality Score": quality_score,
        })

    publications_df = pd.DataFrame(rows)

    total_publications = len(rows)
    journal_count = sum(1 for row in rows if row["Type"] == "Journal")
    conference_count = sum(1 for row in rows if row["Type"] == "Conference")
    indexed_count = sum(1 for row in rows if row["Indexing"] != "Unknown")

    if total_publications > 0:
        research_score = round(sum(row["Quality Score"] for row in rows) / total_publications, 2)
    else:
        research_score = 0
        missing_info.append("No publications found in CV")

    if research_score >= 80:
        strength = "strong"
    elif research_score >= 60:
        strength = "moderate"
    elif research_score > 0:
        strength = "basic"
    else:
        strength = "insufficient"

    summary = (
        f"The candidate has {total_publications} detected publication(s), including "
        f"{journal_count} journal paper(s) and {conference_count} conference paper(s). "
        f"{indexed_count} publication(s) were matched with indexing/ranking lookup data. "
        f"Overall research profile appears {strength} with a research score of {research_score}/100."
    )

    return {
        "publications_table": publications_df,
        "research_score": research_score,
        "total_publications": total_publications,
        "journal_count": journal_count,
        "conference_count": conference_count,
        "indexed_count": indexed_count,
        "missing_info": missing_info,
        "summary": summary,
    }