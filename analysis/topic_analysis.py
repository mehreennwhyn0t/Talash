import pandas as pd


TOPIC_KEYWORDS = {
    "Machine Learning / AI": [
        "machine learning", "deep learning", "artificial intelligence", "ai",
        "neural network", "classification", "prediction", "computer vision",
        "natural language processing", "nlp"
    ],
    "Healthcare / Medical": [
        "health", "healthcare", "medical", "clinical", "patient",
        "disease", "diagnosis", "hospital", "cancer", "diabetes"
    ],
    "Education": [
        "education", "student", "learning", "teaching", "academic",
        "curriculum", "classroom", "e-learning"
    ],
    "Cybersecurity": [
        "security", "cybersecurity", "privacy", "attack", "encryption",
        "malware", "intrusion", "authentication"
    ],
    "Data Science": [
        "data mining", "analytics", "big data", "database",
        "data science", "visualization", "clustering"
    ],
    "Software Engineering": [
        "software", "requirements", "testing", "agile",
        "software engineering", "programming", "development"
    ],
}


def _safe_text(value):
    if value is None:
        return ""
    return str(value).strip()


def _publication_title(pub):
    if isinstance(pub, dict):
        return _safe_text(pub.get("title", ""))
    return _safe_text(pub)


def _detect_topic(title):
    title_lower = title.lower()

    for topic, keywords in TOPIC_KEYWORDS.items():
        for keyword in keywords:
            if keyword in title_lower:
                return topic

    return "Other / Unclear"


def analyze_topic_variability(publications):
    """
    Analyze publication titles and group them into research themes.
    Input: list of publications.
    Output: topic table, dominant topic, diversity score, and summary.
    """

    if publications is None:
        publications = []

    topic_counts = {}

    for pub in publications:
        title = _publication_title(pub)
        topic = _detect_topic(title)
        topic_counts[topic] = topic_counts.get(topic, 0) + 1

    total = sum(topic_counts.values())

    rows = []
    for topic, count in topic_counts.items():
        percentage = round((count / total) * 100, 2) if total else 0
        rows.append({
            "Topic": topic,
            "Publication Count": count,
            "Percentage": percentage
        })

    topic_table = pd.DataFrame(rows)

    if not topic_table.empty:
        dominant_topic = topic_table.sort_values(
            by="Publication Count",
            ascending=False
        ).iloc[0]["Topic"]
    else:
        dominant_topic = "No publications found"

    unique_topics = len(topic_counts)

    if total == 0:
        diversity_score = 0
        diversity_label = "Insufficient Data"
    elif unique_topics == 1:
        diversity_score = 40
        diversity_label = "Highly Focused"
    elif unique_topics == 2:
        diversity_score = 65
        diversity_label = "Moderately Diverse"
    elif unique_topics == 3:
        diversity_score = 80
        diversity_label = "Diverse"
    else:
        diversity_score = 90
        diversity_label = "Highly Diverse / Interdisciplinary"

    summary = (
        f"The dominant research area is {dominant_topic}. "
        f"The candidate's publication profile covers {unique_topics} topic area(s), "
        f"indicating a {diversity_label.lower()} research profile. "
        f"Topic diversity score is {diversity_score}/100."
    )

    return {
        "topic_table": topic_table,
        "dominant_topic": dominant_topic,
        "unique_topics": unique_topics,
        "diversity_score": diversity_score,
        "diversity_label": diversity_label,
        "summary": summary,
    }