def extract_year(text):
    for word in text.split():
        if word.isdigit() and len(word) == 4:
            return word
    return None


def research_analysis(parsed_data):
    publications = parsed_data.get("publications", [])

    total = len(publications)

    journal = 0
    conference = 0

    for pub in publications:
        pub_lower = pub.lower()

        if "journal" in pub_lower:
            journal += 1
        elif "conference" in pub_lower:
            conference += 1

    years = {}

    for pub in publications:
        year = extract_year(pub)
        if year:
            years[year] = years.get(year, 0) + 1

    return {
        "total_publications": total,
        "journal_count": journal,
        "conference_count": conference,
        "publications_by_year": years,
        "research_summary": f"{total} publications found"
    }