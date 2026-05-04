"""
ranking_module.py — Full-scale quantifiable candidate ranking module.

Aggregates scores from all TALASH analysis modules into a weighted
composite score, produces a ranked leaderboard, and generates an
evidence-based ranking justification for each candidate.

Weight breakdown (total = 100):
  Education        20
  Experience       20
  Research         25
  Topic/Coauthor   10
  Supervision/IP   10
  Skill Alignment  15
"""

import pandas as pd


# ── Weights ───────────────────────────────────────────────────────────────────
WEIGHTS = {
    "education":    0.20,
    "experience":   0.20,
    "research":     0.25,
    "topic":        0.05,
    "coauthor":     0.05,
    "supervision":  0.10,
    "skill":        0.15,
}


# ── Score extractors (safe, never crash) ─────────────────────────────────────

def _edu_score(edu):
    """0–100 from education analysis."""
    strength_map = {"strong": 85, "moderate": 65, "fair": 45, "weak": 25, "": 30}
    base = strength_map.get(str(edu.get("academic_strength", "")).lower(), 30)
    # Bonus for PhD
    qual = str(edu.get("highest_qualification", "")).lower()
    if "phd" in qual:
        base = min(base + 10, 100)
    elif "ms" in qual or "msc" in qual or "mphil" in qual:
        base = min(base + 5, 100)
    # Penalty for unjustified gaps
    gaps = [g for g in edu.get("educational_gaps", []) if not g.get("justified")]
    base = max(base - len(gaps) * 5, 0)
    return round(base, 1)


def _exp_score(exp):
    """0–100 from experience analysis."""
    years = exp.get("total_experience_years", 0) or 0
    # Base: cap at 20 years → 70 points
    base = min(years / 20 * 70, 70)
    # Progression bonus
    prog = str(exp.get("career_progression_label", "")).lower()
    if "strong upward" in prog:
        base += 20
    elif "moderate upward" in prog:
        base += 12
    elif "lateral" in prog:
        base += 5
    # Penalty for gaps
    sig_gaps = [g for g in exp.get("employment_gaps", []) if g.get("severity") == "significant"]
    base = max(base - len(sig_gaps) * 8, 0)
    return round(min(base, 100), 1)


def _research_score(res):
    """0–100 from research analysis."""
    return round(float(res.get("research_score", 0) or 0), 1)


def _topic_score(topic):
    """0–100 from topic variability analysis."""
    return round(float(topic.get("diversity_score", 0) or 0), 1)


def _coauthor_score(coauthor):
    """0–100 from co-author analysis."""
    return round(float(coauthor.get("collaboration_score", 0) or 0), 1)


def _supervision_score(sbp):
    """0–100 from supervision/books/patents."""
    return round(float(sbp.get("score", 0) or 0), 1)


def _skill_score(skill_alignment):
    """0–100 from skill alignment analysis."""
    return round(float(skill_alignment.get("overall_skill_score", 0) or 0), 1)


# ── Main ranking function ─────────────────────────────────────────────────────

def rank_candidates(results):
    """
    Compute a weighted composite score for each candidate and return a ranked
    leaderboard DataFrame plus per-candidate score breakdowns.

    Input:  results — list of processed result dicts from streamlit_app
    Output: {
        "leaderboard":   pd.DataFrame (ranked),
        "breakdowns":    list of score breakdown dicts,
        "top_candidate": name of #1 ranked candidate,
        "summary":       str,
    }
    """
    if not results:
        return {
            "leaderboard":   pd.DataFrame(),
            "breakdowns":    [],
            "top_candidate": None,
            "summary":       "No candidates to rank.",
        }

    rows       = []
    breakdowns = []

    for r in results:
        name = (
            r.get("profile", {})
             .get("personal_information", {})
             .get("name", r.get("filename", "Unknown"))
        )

        edu_s    = _edu_score(r.get("education", {}))
        exp_s    = _exp_score(r.get("experience", {}))
        res_s    = _research_score(r.get("research", {}))
        top_s    = _topic_score(r.get("topic_analysis", {}))
        co_s     = _coauthor_score(r.get("coauthor_analysis", {}))
        sbp_s    = _supervision_score(r.get("supervision_books_patents", {}))
        skl_s    = _skill_score(r.get("skill_alignment", {}))

        composite = round(
            edu_s  * WEIGHTS["education"]  +
            exp_s  * WEIGHTS["experience"] +
            res_s  * WEIGHTS["research"]   +
            top_s  * WEIGHTS["topic"]      +
            co_s   * WEIGHTS["coauthor"]   +
            sbp_s  * WEIGHTS["supervision"]+
            skl_s  * WEIGHTS["skill"],
            2
        )

        # Suitability from summary
        suitability = r.get("summary", {}).get("suitability_label", "N/A")

        rows.append({
            "Candidate":          name,
            "Composite Score":    composite,
            "Suitability":        suitability,
            "Education (20%)":    edu_s,
            "Experience (20%)":   exp_s,
            "Research (25%)":     res_s,
            "Topic/Diversity (5%)": top_s,
            "Collaboration (5%)": co_s,
            "Supervision/IP (10%)": sbp_s,
            "Skill Alignment (15%)": skl_s,
        })

        breakdowns.append({
            "name":       name,
            "composite":  composite,
            "edu":        edu_s,
            "exp":        exp_s,
            "research":   res_s,
            "topic":      top_s,
            "coauthor":   co_s,
            "supervision":sbp_s,
            "skill":      skl_s,
            "suitability":suitability,
        })

    df = pd.DataFrame(rows).sort_values("Composite Score", ascending=False).reset_index(drop=True)
    df.insert(0, "Rank", range(1, len(df) + 1))

    top = df.iloc[0]["Candidate"] if not df.empty else "N/A"
    top_score = df.iloc[0]["Composite Score"] if not df.empty else 0

    # Summary narrative
    if len(results) == 1:
        summary_text = (
            f"{top} has a composite score of {top_score}/100 "
            f"based on weighted analysis across education, experience, research, "
            f"topic diversity, collaboration, supervision, and skill alignment."
        )
    else:
        runner = df.iloc[1]["Candidate"] if len(df) > 1 else "N/A"
        runner_score = df.iloc[1]["Composite Score"] if len(df) > 1 else 0
        gap = round(top_score - runner_score, 1)
        summary_text = (
            f"Top-ranked candidate: {top} (score: {top_score}/100). "
            f"Runner-up: {runner} (score: {runner_score}/100). "
            f"Score gap: {gap} points. "
            f"Rankings are based on a weighted composite across 7 dimensions: "
            f"education (20%), experience (20%), research (25%), "
            f"topic diversity (5%), co-author collaboration (5%), "
            f"supervision/books/patents (10%), and skill alignment (15%)."
        )

    return {
        "leaderboard":   df,
        "breakdowns":    breakdowns,
        "top_candidate": top,
        "summary":       summary_text,
    }


def generate_ranking_justification(breakdown):
    """
    Generate a per-candidate text justification of their ranking score.
    """
    name = breakdown["name"]
    parts = [f"**{name}** — Composite Score: {breakdown['composite']}/100\n"]

    score_labels = [
        ("Education",              breakdown["edu"],         20, "academic qualifications and progression"),
        ("Experience",             breakdown["exp"],         20, "professional timeline and career growth"),
        ("Research",               breakdown["research"],    25, "publication quality and output"),
        ("Topic Diversity",        breakdown["topic"],       5,  "breadth of research themes"),
        ("Collaboration",          breakdown["coauthor"],    5,  "co-author network and teamwork"),
        ("Supervision & IP",       breakdown["supervision"], 10, "student supervision, books, and patents"),
        ("Skill Alignment",        breakdown["skill"],       15, "evidence-backed skill claims"),
    ]

    for label, score, weight, desc in score_labels:
        weighted = round(score * weight / 100, 1)
        if score >= 75:
            qualifier = "Strong"
        elif score >= 50:
            qualifier = "Moderate"
        else:
            qualifier = "Weak"
        parts.append(
            f"- **{label}** ({weight}% weight): {score}/100 → "
            f"{weighted} weighted points — {qualifier} {desc}."
        )

    return "\n".join(parts)