import re
import pandas as pd
from collections import Counter


def _safe_text(value):
    if value is None:
        return ""
    return str(value).strip()


def _split_authors(authors_text):
    authors_text = _safe_text(authors_text)

    if not authors_text:
        return []

    authors = re.split(r",|;|\band\b", authors_text)
    authors = [author.strip() for author in authors if author.strip()]

    return authors


def _get_authors(pub):
    if isinstance(pub, dict):
        return _safe_text(pub.get("authors", ""))
    return ""


def analyze_coauthors(publications, candidate_name=""):
    """
    Analyze collaboration pattern from publication authors.
    Input: publications list and optional candidate name.
    Output: coauthor table, collaboration metrics, score, and summary.
    """

    if publications is None:
        publications = []

    candidate_lower = _safe_text(candidate_name).lower()

    all_coauthors = []
    authors_per_paper = []
    single_author_papers = 0
    multi_author_papers = 0
    missing_authors = []

    for idx, pub in enumerate(publications, start=1):
        authors_text = _get_authors(pub)
        authors = _split_authors(authors_text)

        if not authors:
            missing_authors.append(f"Publication {idx}: missing authors list")
            continue

        authors_per_paper.append(len(authors))

        if len(authors) == 1:
            single_author_papers += 1
        else:
            multi_author_papers += 1

        for author in authors:
            author_lower = author.lower()

            if candidate_lower and (
                candidate_lower in author_lower or author_lower in candidate_lower
            ):
                continue

            all_coauthors.append(author)

    coauthor_counter = Counter(all_coauthors)
    unique_coauthors = len(coauthor_counter)

    frequent_rows = []
    for author, count in coauthor_counter.most_common(10):
        frequent_rows.append({
            "Co-author": author,
            "Shared Publications": count
        })

    frequent_coauthors_table = pd.DataFrame(frequent_rows)

    if authors_per_paper:
        average_authors_per_paper = round(sum(authors_per_paper) / len(authors_per_paper), 2)
    else:
        average_authors_per_paper = 0

    if unique_coauthors == 0:
        collaboration_score = 20
        collaboration_label = "Very Limited Collaboration"
    elif unique_coauthors <= 5:
        collaboration_score = 50
        collaboration_label = "Limited Collaboration"
    elif unique_coauthors <= 15:
        collaboration_score = 75
        collaboration_label = "Good Collaboration Network"
    else:
        collaboration_score = 90
        collaboration_label = "Strong Collaboration Network"

    top_coauthor = (
        frequent_coauthors_table.iloc[0]["Co-author"]
        if not frequent_coauthors_table.empty
        else "None detected"
    )

    summary = (
        f"The candidate has {unique_coauthors} unique detected co-author(s). "
        f"The average number of authors per paper is {average_authors_per_paper}. "
        f"The most frequent collaborator is {top_coauthor}. "
        f"Overall collaboration pattern is classified as {collaboration_label.lower()} "
        f"with a collaboration score of {collaboration_score}/100."
    )

    return {
        "frequent_coauthors_table": frequent_coauthors_table,
        "unique_coauthors": unique_coauthors,
        "average_authors_per_paper": average_authors_per_paper,
        "single_author_papers": single_author_papers,
        "multi_author_papers": multi_author_papers,
        "collaboration_score": collaboration_score,
        "collaboration_label": collaboration_label,
        "missing_info": missing_authors,
        "summary": summary,
    }