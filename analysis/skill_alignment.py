"""
skill_alignment.py

Milestone 3 module for TALASH.

Features:
- Skill-to-experience alignment
- Skill-to-publication alignment
- Skill-to-education alignment
- Skill-to-job-description alignment
- Evidence classification
- Candidate skill set comparison
"""

import re
from collections import Counter


DEFAULT_JOB_DESCRIPTION = """
University faculty position requiring teaching, research, curriculum development,
student supervision, publications, machine learning, data analysis, programming,
communication skills, and academic leadership.
"""


SKILL_KEYWORDS = {
    "machine learning": ["machine learning", "ml", "classification", "prediction", "model"],
    "deep learning": ["deep learning", "neural", "cnn", "rnn", "transformer", "lstm"],
    "natural language processing": ["nlp", "natural language", "text mining", "language model"],
    "computer vision": ["computer vision", "image processing", "object detection", "segmentation"],
    "data analysis": ["data analysis", "analytics", "statistical", "data mining", "visualization"],
    "python": ["python"],
    "matlab": ["matlab"],
    "java": ["java"],
    "c++": ["c++", "cpp"],
    "sql": ["sql", "database", "mysql", "postgresql"],
    "research": ["research", "publication", "journal", "conference", "paper"],
    "teaching": ["teaching", "lecturer", "instructor", "professor", "faculty"],
    "curriculum design": ["curriculum", "course design", "course development"],
    "student supervision": ["supervision", "supervisor", "thesis", "ms student", "phd student"],
    "project management": ["project management", "coordinator", "manager", "lead"],
    "communication": ["communication", "presentation", "seminar", "training"],
    "optimization": ["optimization", "genetic algorithm", "particle swarm", "metaheuristic"],
    "cybersecurity": ["cybersecurity", "security", "encryption", "malware", "network security"],
    "networks": ["network", "wireless", "communication system", "iot", "sensor network"],
    "software engineering": ["software engineering", "software development", "web development"],
    "cloud computing": ["cloud", "aws", "azure", "gcp", "cloud computing"],
    "databases": ["database", "sql", "mysql", "postgresql", "mongodb"],
    "artificial intelligence": ["artificial intelligence", "ai", "intelligent system"],
    "signal processing": ["signal processing", "digital signal", "filtering"],
    "internet of things": ["iot", "internet of things", "sensor"],
}


def _clean_text(value):
    if value is None:
        return ""

    if isinstance(value, list):
        return " ".join(_clean_text(item) for item in value)

    if isinstance(value, dict):
        return " ".join(_clean_text(item) for item in value.values())

    return str(value).lower()


def _normalize_skill(skill):
    skill = str(skill).strip().lower()
    skill = re.sub(r"\s+", " ", skill)
    return skill


def _contains_any(text, keywords):
    text = _clean_text(text)
    return any(keyword.lower() in text for keyword in keywords)


def _get_candidate_name(profile):
    personal = profile.get("personal_information", {}) or {}
    return personal.get("name") or profile.get("name") or "Unknown Candidate"


def _get_candidate_skills(profile):
    skills = profile.get("skills", [])

    if isinstance(skills, str):
        skills = re.split(r",|;|\n", skills)

    cleaned = []

    for skill in skills:
        skill = _normalize_skill(skill)
        if skill:
            cleaned.append(skill)

    return sorted(set(cleaned))


def _build_evidence_text(profile, job_description=None):
    return {
        "experience_text": _clean_text(profile.get("experience", [])),
        "publication_text": _clean_text(profile.get("publications", [])),
        "education_text": _clean_text(profile.get("education", [])),
        "supervision_text": _clean_text(profile.get("supervision", [])),
        "books_text": _clean_text(profile.get("books", [])),
        "patents_text": _clean_text(profile.get("patents", [])),
        "job_text": _clean_text(job_description or DEFAULT_JOB_DESCRIPTION),
    }


def _infer_skill_keywords(skill):
    normalized = _normalize_skill(skill)

    if normalized in SKILL_KEYWORDS:
        return SKILL_KEYWORDS[normalized]

    for known_skill, keywords in SKILL_KEYWORDS.items():
        if normalized in known_skill or known_skill in normalized:
            return keywords + [normalized]

    return [normalized]


def analyze_skill_alignment(profile, job_description=None):
    """
    Analyze whether claimed skills are supported by candidate evidence.
    """
    candidate_skills = _get_candidate_skills(profile)
    evidence = _build_evidence_text(profile, job_description)

    skill_table = []
    strongly_evidenced = []
    partially_evidenced = []
    weakly_evidenced = []
    unsupported = []

    for skill in candidate_skills:
        keywords = _infer_skill_keywords(skill)
        evidence_sources = []

        if _contains_any(evidence["experience_text"], keywords):
            evidence_sources.append("experience")

        if _contains_any(evidence["publication_text"], keywords):
            evidence_sources.append("publications")

        if _contains_any(evidence["education_text"], keywords):
            evidence_sources.append("education")

        if _contains_any(evidence["supervision_text"], keywords):
            evidence_sources.append("supervision")

        if _contains_any(evidence["books_text"], keywords):
            evidence_sources.append("books")

        if _contains_any(evidence["patents_text"], keywords):
            evidence_sources.append("patents")

        if _contains_any(evidence["job_text"], keywords):
            evidence_sources.append("job_description")

        profile_evidence_count = len([
            source for source in evidence_sources
            if source != "job_description"
        ])

        job_relevant = "job_description" in evidence_sources

        if profile_evidence_count >= 2 and job_relevant:
            category = "Strongly Evidenced"
            score = 100
            strongly_evidenced.append(skill)

        elif profile_evidence_count >= 2:
            category = "Strongly Evidenced"
            score = 90
            strongly_evidenced.append(skill)

        elif profile_evidence_count == 1 and job_relevant:
            category = "Partially Evidenced"
            score = 75
            partially_evidenced.append(skill)

        elif profile_evidence_count == 1:
            category = "Partially Evidenced"
            score = 65
            partially_evidenced.append(skill)

        elif job_relevant:
            category = "Weakly Evidenced"
            score = 45
            weakly_evidenced.append(skill)

        else:
            category = "Unsupported"
            score = 20
            unsupported.append(skill)

        skill_table.append({
            "skill": skill,
            "category": category,
            "evidence_sources": evidence_sources,
            "job_relevant": job_relevant,
            "score": score,
        })

    if candidate_skills:
        overall_score = round(
            sum(item["score"] for item in skill_table) / len(candidate_skills),
            2,
        )
    else:
        overall_score = 0

    if overall_score >= 80:
        label = "Strong Skill Alignment"
    elif overall_score >= 60:
        label = "Moderate Skill Alignment"
    elif overall_score >= 40:
        label = "Weak Skill Alignment"
    else:
        label = "Insufficient / Unsupported Skills"

    return {
        "candidate_name": _get_candidate_name(profile),
        "total_claimed_skills": len(candidate_skills),
        "overall_skill_score": overall_score,
        "alignment_label": label,
        "strongly_evidenced": strongly_evidenced,
        "partially_evidenced": partially_evidenced,
        "weakly_evidenced": weakly_evidenced,
        "unsupported": unsupported,
        "skill_table": skill_table,
        "summary": generate_skill_alignment_summary(
            candidate_skills,
            strongly_evidenced,
            partially_evidenced,
            weakly_evidenced,
            unsupported,
            label,
            overall_score,
        ),
    }


def generate_skill_alignment_summary(
    skills,
    strongly_evidenced,
    partially_evidenced,
    weakly_evidenced,
    unsupported,
    label,
    score,
):
    if not skills:
        return "No explicit skills were extracted from the CV, so skill alignment could not be fully evaluated."

    return (
        f"The candidate has {len(skills)} claimed skill(s). "
        f"{len(strongly_evidenced)} are strongly evidenced, "
        f"{len(partially_evidenced)} are partially evidenced, "
        f"{len(weakly_evidenced)} are weakly evidenced, and "
        f"{len(unsupported)} appear unsupported by the extracted profile. "
        f"Overall skill alignment is classified as '{label}' with a score of {score}/100."
    )


def get_skill_score(profile, job_description=None):
    return analyze_skill_alignment(profile, job_description).get("overall_skill_score", 0)


def compare_candidate_skill_sets(profiles, job_description=None):
    """
    Compare skill sets across multiple candidates.
    """
    candidate_results = []
    all_skill_sets = {}
    all_skills_counter = Counter()

    for profile in profiles:
        name = _get_candidate_name(profile)
        analysis = analyze_skill_alignment(profile, job_description=job_description)

        skill_names = [
            item["skill"]
            for item in analysis.get("skill_table", [])
        ]

        skill_set = set(skill_names)

        all_skill_sets[name] = skill_set
        all_skills_counter.update(skill_set)

        candidate_results.append({
            "candidate_name": name,
            "total_claimed_skills": analysis.get("total_claimed_skills", 0),
            "strongly_evidenced_count": len(analysis.get("strongly_evidenced", [])),
            "partially_evidenced_count": len(analysis.get("partially_evidenced", [])),
            "weakly_evidenced_count": len(analysis.get("weakly_evidenced", [])),
            "unsupported_count": len(analysis.get("unsupported", [])),
            "skill_score": analysis.get("overall_skill_score", 0),
            "alignment_label": analysis.get("alignment_label", "Unknown"),
            "strongly_evidenced": analysis.get("strongly_evidenced", []),
            "partially_evidenced": analysis.get("partially_evidenced", []),
            "weakly_evidenced": analysis.get("weakly_evidenced", []),
            "unsupported": analysis.get("unsupported", []),
        })

    if all_skill_sets:
        if len(all_skill_sets) > 1:
            common_skills = sorted(set.intersection(*all_skill_sets.values()))
        else:
            common_skills = sorted(next(iter(all_skill_sets.values())))
    else:
        common_skills = []

    unique_skills_by_candidate = {}

    for candidate, skills in all_skill_sets.items():
        other_skills = set()

        for other_candidate, other_candidate_skills in all_skill_sets.items():
            if other_candidate != candidate:
                other_skills.update(other_candidate_skills)

        unique_skills_by_candidate[candidate] = sorted(skills - other_skills)

    top_skills = [
        {
            "skill": skill,
            "candidate_count": count,
        }
        for skill, count in all_skills_counter.most_common()
    ]

    ranked_by_skill_score = sorted(
        candidate_results,
        key=lambda x: x["skill_score"],
        reverse=True,
    )

    best_skill_match = ranked_by_skill_score[0] if ranked_by_skill_score else None

    return {
        "candidate_skill_summary": candidate_results,
        "common_skills": common_skills,
        "unique_skills_by_candidate": unique_skills_by_candidate,
        "top_skills": top_skills,
        "ranked_by_skill_score": ranked_by_skill_score,
        "best_skill_match": best_skill_match,
        "summary": generate_skill_comparison_summary(
            candidate_results,
            common_skills,
            top_skills,
            best_skill_match,
        ),
    }


def generate_skill_comparison_summary(
    candidate_results,
    common_skills,
    top_skills,
    best_skill_match,
):
    if not candidate_results:
        return "No candidate skill data is available for comparison."

    total_candidates = len(candidate_results)

    if best_skill_match:
        best_name = best_skill_match["candidate_name"]
        best_score = best_skill_match["skill_score"]
    else:
        best_name = "N/A"
        best_score = 0

    top_skill_names = [item["skill"] for item in top_skills[:5]]

    return (
        f"Skill comparison was performed for {total_candidates} candidate(s). "
        f"The strongest skill match is {best_name} with a skill alignment score of {best_score}/100. "
        f"Common skills across candidates include: "
        f"{', '.join(common_skills) if common_skills else 'none detected'}. "
        f"The most frequent skills across the pool are: "
        f"{', '.join(top_skill_names) if top_skill_names else 'none detected'}."
    )