"""
research_analysis.py

Research profile analysis.
Covers: publication counting, journal/conference classification,
authorship role analysis, publication timeline, and research summary.
Uses LLM when available for enhanced analysis.
"""

import re


def extract_year(text):
    """Extract a 4-digit year from text."""
    if not text:
        return None
    for word in str(text).split():
        if word.isdigit() and len(word) == 4:
            return word
    match = re.search(r'\b((?:19|20)\d{2})\b', str(text))
    return match.group(1) if match else None


def classify_publication_type(pub):
    """Classify a publication as journal or conference."""
    venue = str(pub.get("venue", "")).lower()
    title = str(pub.get("title", "")).lower()
    pub_type = str(pub.get("type", "")).lower()

    if "journal" in pub_type or "journal" in venue:
        return "journal"
    elif "conference" in pub_type or "conference" in venue:
        return "conference"
    elif any(kw in venue or kw in title for kw in
             ["symposium", "workshop", "proceedings"]):
        return "conference"
    elif any(kw in venue for kw in
             ["ieee trans", "acm trans", "elsevier", "springer", "wiley"]):
        return "journal"
    return "unknown"


def determine_authorship_role(pub, candidate_name=""):
    """Determine the candidate's authorship role in a publication."""
    position = str(pub.get("candidate_position", "")).lower()
    if position and position != "unknown":
        return position

    authors = pub.get("authors", [])
    if not authors or not candidate_name:
        return "unknown"

    candidate_lower = candidate_name.lower()
    candidate_parts = candidate_lower.split()

    for i, author in enumerate(authors):
        author_lower = author.lower()
        if (candidate_lower in author_lower
                or any(part in author_lower for part in candidate_parts if len(part) > 2)):
            if i == 0:
                return "first"
            elif i == len(authors) - 1:
                return "corresponding"  # Common convention
            else:
                return "co-author"

    return "unknown"


def analyze_publication_venues(publications):
    """Analyze publication venue quality indicators."""
    venues = {}
    for pub in publications:
        venue = pub.get("venue", "Unknown")
        if venue:
            venues[venue] = venues.get(venue, 0) + 1

    impact_factors = []
    for pub in publications:
        if_str = pub.get("impact_factor", "")
        if if_str:
            try:
                impact_factors.append(float(if_str))
            except (ValueError, TypeError):
                pass

    return {
        "venue_distribution": venues,
        "avg_impact_factor": (
            round(sum(impact_factors) / len(impact_factors), 2)
            if impact_factors else None
        ),
        "max_impact_factor": (
            round(max(impact_factors), 2) if impact_factors else None
        ),
        "papers_with_if": len(impact_factors),
    }


def research_analysis(parsed_data, candidate_name=""):
    """
    Main entry point for research profile analysis.
    Returns comprehensive research analysis dict.
    """
    publications = parsed_data.get("publications", [])

    if not publications:
        return {
            "total_publications": 0,
            "journal_count": 0,
            "conference_count": 0,
            "unknown_type_count": 0,
            "first_author_count": 0,
            "corresponding_author_count": 0,
            "co_author_count": 0,
            "publications_by_year": {},
            "publications_by_type": {},
            "venue_analysis": {},
            "authorship_summary": "No publications found.",
            "research_themes": [],
            "publication_table": [],
            "research_summary": "No research publications detected in the CV.",
        }

    if not candidate_name:
        candidate_name = parsed_data.get(
            "personal_information", {}
        ).get("name", "")

    # Classify publications
    journal_count = 0
    conference_count = 0
    unknown_count = 0
    first_author = 0
    corresponding = 0
    co_author = 0

    by_year = {}
    by_type = {"journal": 0, "conference": 0, "unknown": 0}
    pub_table = []

    for pub in publications:
        # Type classification
        pub_type = classify_publication_type(pub)
        if pub_type == "journal":
            journal_count += 1
            by_type["journal"] += 1
        elif pub_type == "conference":
            conference_count += 1
            by_type["conference"] += 1
        else:
            unknown_count += 1
            by_type["unknown"] += 1

        # Authorship role
        role = determine_authorship_role(pub, candidate_name)
        if role == "first":
            first_author += 1
        elif role == "corresponding":
            corresponding += 1
        elif role == "co-author":
            co_author += 1

        # Year tracking
        year = pub.get("year", "") or extract_year(pub.get("title", ""))
        if year:
            by_year[str(year)] = by_year.get(str(year), 0) + 1

        # Build table row
        title = pub.get("title", "N/A")
        if isinstance(title, str) and len(title) > 80:
            title = title

        pub_table.append({
            "Title": title,
            "Type": pub_type.title(),
            "Venue": str(pub.get("venue", "N/A")),
            "Year": year or "N/A",
            "IF": pub.get("impact_factor", "N/A"),
            "Role": role.title(),
        })

    # Venue analysis
    venue_analysis = analyze_publication_venues(publications)

    # Research themes (keyword-based)
    theme_keywords = {
        "Machine Learning": ["machine learning", "ml", "neural network", "deep learning", "ann", "cnn", "rnn"],
        "Wireless Communication": ["wireless", "5g", "noma", "ofdm", "communication", "antenna", "mimo"],
        "IoT & Sensors": ["iot", "sensor", "wsn", "wireless sensor"],
        "Computer Vision": ["image", "vision", "object detection", "segmentation"],
        "NLP": ["nlp", "natural language", "text", "sentiment"],
        "Optimization": ["optimization", "convex", "resource allocation", "scheduling"],
        "Networking": ["routing", "network", "clustering", "protocol"],
        "Signal Processing": ["signal processing", "filter", "spectrum"],
        "Data Science": ["data", "prediction", "predictive", "analytics", "pm2.5"],
        "Cybersecurity": ["security", "cyber", "intrusion", "encryption"],
        "Power Systems": ["power", "energy", "renewable", "grid"],
    }

    theme_counts = {}
    for pub in publications:
        text = f"{pub.get('title', '')} {pub.get('venue', '')}".lower()
        for theme, keywords in theme_keywords.items():
            if any(kw in text for kw in keywords):
                theme_counts[theme] = theme_counts.get(theme, 0) + 1

    research_themes = sorted(theme_counts.items(), key=lambda x: -x[1])
    dominant_theme = research_themes[0][0] if research_themes else "Not determined"

    # Authorship summary
    total = len(publications)
    authorship_parts = []
    if first_author:
        authorship_parts.append(f"{first_author} as first author")
    if corresponding:
        authorship_parts.append(f"{corresponding} as corresponding author")
    if co_author:
        authorship_parts.append(f"{co_author} as co-author")

    authorship_summary = (
        f"Out of {total} publication(s): " + ", ".join(authorship_parts)
        if authorship_parts
        else f"{total} publication(s) - authorship roles could not be determined"
    )

    # Research summary
    summary_parts = [f"{total} publication(s) found"]
    if journal_count:
        summary_parts.append(f"{journal_count} journal paper(s)")
    if conference_count:
        summary_parts.append(f"{conference_count} conference paper(s)")
    if venue_analysis.get("avg_impact_factor"):
        summary_parts.append(
            f"average impact factor: {venue_analysis['avg_impact_factor']}"
        )
    if dominant_theme != "Not determined":
        summary_parts.append(f"primary research area: {dominant_theme}")

    research_summary = ". ".join(summary_parts) + "."

    return {
        "total_publications": total,
        "journal_count": journal_count,
        "conference_count": conference_count,
        "unknown_type_count": unknown_count,
        "first_author_count": first_author,
        "corresponding_author_count": corresponding,
        "co_author_count": co_author,
        "publications_by_year": dict(sorted(by_year.items())),
        "publications_by_type": by_type,
        "venue_analysis": venue_analysis,
        "authorship_summary": authorship_summary,
        "research_themes": research_themes,
        "dominant_theme": dominant_theme,
        "publication_table": pub_table,
        "research_summary": research_summary,
    }