"""
TALASH - Smart CV Analyzer | Streamlit Dashboard
Milestone 2: Full intermediate web application with batch processing,
tables, charts, email drafts, and candidate comparison.
"""

import json
import tempfile
from pathlib import Path

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from preprocessing.pdf_reader import extract_text_from_pdf
from preprocessing.parser import parse_candidate_profile
from analysis.education_analysis import analyze_education_profile
from analysis.experience_analysis import analyze_experience
from analysis.research_analysis import research_analysis
from analysis.email_drafter import analyze_missing_and_draft_email, batch_draft_emails
from analysis.summary_generator import generate_summary, generate_llm_summary

# PAGE CONFIG & CUSTOM CSS
st.set_page_config(page_title="TALASH - Smart HR Recruitment", layout="wide", page_icon="")

st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem; font-weight: 700;
        background: linear-gradient(90deg, #1e3a5f, #2980b9);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin-bottom: 0;
    }
    .sub-header { color: #7f8c8d; font-size: 1.1rem; margin-top: -10px; }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px; border-radius: 12px; color: white; text-align: center;
    }
    .metric-card h2 { margin: 0; font-size: 2rem; }
    .metric-card p { margin: 5px 0 0 0; font-size: 0.9rem; opacity: 0.9; }
    .strength-badge {
        background: #27ae60; color: white; padding: 4px 12px;
        border-radius: 20px; display: inline-block; margin: 2px;
    }
    .concern-badge {
        background: #e74c3c; color: white; padding: 4px 12px;
        border-radius: 20px; display: inline-block; margin: 2px;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px; border-radius: 8px 8px 0 0;
    }
</style>
""", unsafe_allow_html=True)

INPUT_DIR = Path("data/input_cvs")


# PROCESSING FUNCTIONS
def process_single_cv(pdf_path: Path) -> dict:
    """Process a single CV and return full analysis."""
    text = extract_text_from_pdf(pdf_path)
    profile = parse_candidate_profile(text, use_llm=True)
    edu = analyze_education_profile(profile)
    exp = analyze_experience(profile)
    res = research_analysis(profile)
    email_result = analyze_missing_and_draft_email(profile)
    summary = generate_summary(edu, exp, res, email_result["missing_info_analysis"])

    return {
        "filename": pdf_path.name,
        "raw_text": text,
        "profile": profile,
        "education": edu,
        "experience": exp,
        "research": res,
        "email_result": email_result,
        "summary": summary,
    }


def process_batch(pdf_files: list) -> list:
    """Process multiple CVs and return list of results."""
    results = []
    progress = st.progress(0, text="Processing CVs...")
    for i, pdf_path in enumerate(pdf_files):
        try:
            result = process_single_cv(pdf_path)
            results.append(result)
        except Exception as e:
            st.warning(f"Failed to process {pdf_path.name}: {e}")
        progress.progress((i + 1) / len(pdf_files), text=f"Processed {i+1}/{len(pdf_files)}")
    progress.empty()
    return results


# RENDERING FUNCTIONS
def render_metric_cards(results):
    """Display summary metric cards."""
    cols = st.columns(4)
    with cols[0]:
        st.metric("CVs Processed", len(results))
    with cols[1]:
        total_pubs = sum(r["research"]["total_publications"] for r in results)
        st.metric("Total Publications", total_pubs)
    with cols[2]:
        strong = sum(1 for r in results if r["summary"]["suitability_label"] == "Strong Candidate")
        st.metric("Strong Candidates", strong)
    with cols[3]:
        avg_exp = sum(r["experience"].get("total_experience_years", 0) for r in results)
        avg_exp = round(avg_exp / len(results), 1) if results else 0
        st.metric("Avg Experience (yrs)", avg_exp)


def render_education_tab(result):
    """Render education analysis for a single candidate."""
    edu = result["education"]
    st.subheader("Educational Profile Analysis")

    # Summary metrics
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f"<div style='margin-bottom: 15px;'><span style='font-size: 0.9rem; color: #a0a0a0;'>Highest Qualification</span><br><span style='font-size: 1.6rem; font-weight: 600; line-height: 1.2;'>{edu.get('highest_qualification', 'N/A')}</span></div>", unsafe_allow_html=True)
    c2.markdown(f"<div style='margin-bottom: 15px;'><span style='font-size: 0.9rem; color: #a0a0a0;'>Academic Strength</span><br><span style='font-size: 1.6rem; font-weight: 600; line-height: 1.2;'>{edu.get('academic_strength', 'N/A').title()}</span></div>", unsafe_allow_html=True)
    c3.markdown(f"<div style='margin-bottom: 15px;'><span style='font-size: 0.9rem; color: #a0a0a0;'>Progression Trend</span><br><span style='font-size: 1.6rem; font-weight: 600; line-height: 1.2;'>{edu.get('progression_trend', 'N/A').title()}</span></div>", unsafe_allow_html=True)
    c4.markdown(f"<div style='margin-bottom: 15px;'><span style='font-size: 0.9rem; color: #a0a0a0;'>Avg Score (/100)</span><br><span style='font-size: 1.6rem; font-weight: 600; line-height: 1.2;'>{edu.get('average_normalized_score', 'N/A')}</span></div>", unsafe_allow_html=True)

    # Education table
    if edu.get("education_table"):
        st.markdown("#### Education Records")
        df = pd.DataFrame(edu["education_table"])
        st.dataframe(df, use_container_width=True, hide_index=True)

    # Degree sequence
    st.markdown(f"**Degree Sequence:** {edu.get('degree_sequence', 'N/A')}")
    st.markdown(f"**Specialization:** {edu.get('specialization_summary', 'N/A')}")

    # Score chart
    levels = edu.get("education_levels", [])
    scores = [l for l in levels if l.get("normalized_score")]
    if scores:
        chart_df = pd.DataFrame([{
            "Degree": s["degree"],
            "Score (/100)": s["normalized_score"]
        } for s in scores])
        fig = px.bar(chart_df, x="Degree", y="Score (/100)",
                     title="Academic Performance Across Levels",
                     color="Score (/100)",
                     color_continuous_scale="Viridis")
        fig.update_layout(height=350)
        st.plotly_chart(fig, use_container_width=True)

    # Educational gaps
    gaps = edu.get("educational_gaps", [])
    if gaps:
        st.markdown("#### Educational Gaps Detected")
        for g in gaps:
            status = "Justified" if g["justified"] else "Unexplained"
            st.markdown(
                f"- **{g['between']}** - {g['gap_years']} year(s) gap - "
                f"{status}: {g.get('justification', '')}"
            )
    else:
        st.success("No significant educational gaps detected.")

    # Institution quality
    inst = edu.get("institution_quality", [])
    if inst:
        st.markdown("#### Institution Quality")
        for i in inst:
            q = i.get("quality", {})
            st.markdown(
                f"- **{i['institution']}** ({i['degree']}) - "
                f"{q.get('label', 'N/A')} | QS: {q.get('qs_range', 'N/A')}"
            )

    # Interpretation
    st.info(f"**Assessment:** {edu.get('interpretation', 'N/A')}")


def render_experience_tab(result):
    """Render experience analysis for a single candidate."""
    exp = result["experience"]
    st.subheader("Professional Experience Analysis")

    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div style='margin-bottom: 15px;'><span style='font-size: 0.9rem; color: #a0a0a0;'>Total Roles</span><br><span style='font-size: 1.6rem; font-weight: 600; line-height: 1.2;'>{exp.get('total_roles', 0)}</span></div>", unsafe_allow_html=True)
    c2.markdown(f"<div style='margin-bottom: 15px;'><span style='font-size: 0.9rem; color: #a0a0a0;'>Total Experience</span><br><span style='font-size: 1.6rem; font-weight: 600; line-height: 1.2;'>{exp.get('total_experience_years', 0)} yrs</span></div>", unsafe_allow_html=True)
    c3.markdown(f"<div style='margin-bottom: 15px;'><span style='font-size: 0.9rem; color: #a0a0a0;'>Career Progression</span><br><span style='font-size: 1.6rem; font-weight: 600; line-height: 1.2;'>{exp.get('career_progression_label', 'N/A')}</span></div>", unsafe_allow_html=True)

    # Experience table
    if exp.get("experience_table"):
        st.markdown("#### Employment Timeline")
        df = pd.DataFrame(exp["experience_table"])
        st.dataframe(df, use_container_width=True, hide_index=True)

    # Employment gaps
    gaps = exp.get("employment_gaps", [])
    if gaps:
        st.markdown("#### Employment Gaps")
        gap_df = pd.DataFrame([{
            "After": f"{g['after_role']} @ {g['after_org']}",
            "Before": f"{g['before_role']} @ {g['before_org']}",
            "Duration": g["gap_readable"],
            "Severity": g["severity"].title(),
            "Justified": "Yes" if g.get("justified") else "No",
        } for g in gaps])
        st.dataframe(gap_df, use_container_width=True, hide_index=True)
    else:
        st.success("No employment gaps detected.")

    # Job overlaps
    overlaps = exp.get("job_overlaps", [])
    if overlaps:
        st.markdown("#### Overlapping Roles")
        for o in overlaps:
            st.warning(
                f"**{o['role_a']}** ({o.get('period_a','')}) ↔ "
                f"**{o['role_b']}** ({o.get('period_b','')}) - "
                f"{o['overlap_months']} month(s) overlap. {o['note']}"
            )

    # Education-employment overlaps
    edu_overlaps = exp.get("education_employment_overlaps", [])
    if edu_overlaps:
        st.markdown("#### Education-Employment Overlaps")
        for o in edu_overlaps:
            st.info(
                f"**{o['role']}** @ {o['organization']} overlaps with "
                f"**{o['degree']}** @ {o['institution']} - "
                f"{o['overlap_months']} month(s). {o['note']}"
            )

    st.markdown(f"**Summary:** {exp.get('continuity_summary', 'N/A')}")


def render_research_tab(result):
    """Render research analysis for a single candidate."""
    res = result["research"]
    st.subheader("Research Profile Analysis")

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f"<div style='margin-bottom: 15px;'><span style='font-size: 0.9rem; color: #a0a0a0;'>Total Publications</span><br><span style='font-size: 1.6rem; font-weight: 600; line-height: 1.2;'>{res.get('total_publications', 0)}</span></div>", unsafe_allow_html=True)
    c2.markdown(f"<div style='margin-bottom: 15px;'><span style='font-size: 0.9rem; color: #a0a0a0;'>Journal Papers</span><br><span style='font-size: 1.6rem; font-weight: 600; line-height: 1.2;'>{res.get('journal_count', 0)}</span></div>", unsafe_allow_html=True)
    c3.markdown(f"<div style='margin-bottom: 15px;'><span style='font-size: 0.9rem; color: #a0a0a0;'>Conference Papers</span><br><span style='font-size: 1.6rem; font-weight: 600; line-height: 1.2;'>{res.get('conference_count', 0)}</span></div>", unsafe_allow_html=True)
    c4.markdown(f"<div style='margin-bottom: 15px;'><span style='font-size: 0.9rem; color: #a0a0a0;'>Dominant Theme</span><br><span style='font-size: 1.6rem; font-weight: 600; line-height: 1.2;'>{res.get('dominant_theme', 'N/A')}</span></div>", unsafe_allow_html=True)

    # Publication table
    if res.get("publication_table"):
        st.markdown("#### Publication Details")
        df = pd.DataFrame(res["publication_table"])
        st.dataframe(df, use_container_width=True, hide_index=True)

    col1, col2 = st.columns(2)

    # Publications by type (pie chart)
    with col1:
        by_type = res.get("publications_by_type", {})
        if any(v > 0 for v in by_type.values()):
            fig = px.pie(
                names=list(by_type.keys()),
                values=list(by_type.values()),
                title="Publications by Type",
                color_discrete_sequence=["#3498db", "#e74c3c", "#95a5a6"]
            )
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)

    # Publications by year (bar chart)
    with col2:
        by_year = res.get("publications_by_year", {})
        if by_year:
            fig = px.bar(
                x=list(by_year.keys()),
                y=list(by_year.values()),
                title="Publications by Year",
                labels={"x": "Year", "y": "Count"},
                color_discrete_sequence=["#2ecc71"]
            )
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)

    # Authorship breakdown
    st.markdown(f"**Authorship:** {res.get('authorship_summary', 'N/A')}")

    # Research themes
    themes = res.get("research_themes", [])
    if themes:
        st.markdown("#### Research Themes")
        theme_df = pd.DataFrame(themes, columns=["Theme", "Papers"])
        fig = px.bar(theme_df, x="Theme", y="Papers",
                     title="Research Theme Distribution",
                     color="Papers", color_continuous_scale="Blues")
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)

    # Venue analysis
    va = res.get("venue_analysis", {})
    if va.get("avg_impact_factor"):
        st.markdown(
            f"**Avg Impact Factor:** {va['avg_impact_factor']} | "
            f"**Max IF:** {va.get('max_impact_factor', 'N/A')} | "
            f"**Papers with IF:** {va.get('papers_with_if', 0)}"
        )

    st.info(f"**Summary:** {res.get('research_summary', 'N/A')}")


def render_email_tab(result):
    """Render missing info and email draft."""
    email_result = result["email_result"]
    missing = email_result["missing_info_analysis"]

    st.subheader(f"Missing Information - {email_result['candidate_name']}")

    c1, c2, c3 = st.columns(3)
    c1.metric("Missing", len(missing.get("missing", [])))
    c2.metric("Incomplete", len(missing.get("incomplete", [])))
    c3.metric("Unclear", len(missing.get("unclear", [])))

    col1, col2 = st.columns(2)
    with col1:
        if missing.get("missing"):
            st.markdown("**Missing Fields:**")
            for m in missing["missing"]:
                st.markdown(f"- {m}")
        if missing.get("incomplete"):
            st.markdown("**Incomplete Fields:**")
            for m in missing["incomplete"]:
                st.markdown(f"- {m}")
        if missing.get("unclear"):
            st.markdown("**Unclear Fields:**")
            for m in missing["unclear"]:
                st.markdown(f"- {m}")

    with col2:
        draft = email_result["email_draft"]
        if draft.get("required"):
            st.text_input("Subject", draft["subject"], key=f"subj_{result['filename']}")
            st.text_area("Email Body", draft["body"], height=350, key=f"body_{result['filename']}")
        else:
            st.success("No missing information - email not required.")


def render_summary_tab(result):
    """Render candidate summary."""
    summary = result["summary"]
    name = result["profile"].get("personal_information", {}).get("name", "Unknown")

    st.subheader(f"Candidate Summary - {name}")

    # Suitability badge
    label = summary.get("suitability_label", "Unknown")
    colors = {
        "Strong Candidate": "#27ae60",
        "Good Candidate": "#2ecc71",
        "Moderate Candidate": "#f39c12",
        "Needs Review": "#e74c3c",
    }
    color = colors.get(label, "#95a5a6")
    st.markdown(
        f'<div style="background:{color}; color:white; padding:12px 24px; '
        f'border-radius:8px; font-size:1.3rem; display:inline-block; '
        f'margin-bottom:16px;">{label}</div>',
        unsafe_allow_html=True
    )

    # Key highlights
    highlights = summary.get("key_highlights", [])
    if highlights:
        hcols = st.columns(len(highlights))
        for i, h in enumerate(highlights):
            hcols[i].info(h)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Strengths")
        for s in summary.get("strengths", []):
            st.markdown(f"- {s}")
        if not summary.get("strengths"):
            st.caption("No notable strengths identified.")
    with col2:
        st.markdown("#### Concerns")
        for c in summary.get("concerns", []):
            st.markdown(f"- {c}")
        if not summary.get("concerns"):
            st.caption("No concerns identified.")

    st.markdown("***")
    st.markdown(f"**Overall Assessment:** {summary.get('overall_assessment', 'N/A')}")


def render_comparison_tab(results):
    """Render side-by-side candidate comparison."""
    st.subheader("Candidate Comparison")

    if len(results) < 2:
        st.info("Upload or process at least 2 CVs to enable comparison.")
        return

    # Comparison table
    comp_data = []
    for r in results:
        name = r["profile"].get("personal_information", {}).get("name", "Unknown")
        edu = r["education"]
        exp = r["experience"]
        res = r["research"]
        summ = r["summary"]

        comp_data.append({
            "Name": name,
            "Suitability": summ.get("suitability_label", "N/A"),
            "Highest Degree": edu.get("highest_qualification", "N/A"),
            "Acad. Strength": edu.get("academic_strength", "N/A").title(),
            "Avg Score": edu.get("average_normalized_score", "N/A"),
            "Total Exp (yrs)": exp.get("total_experience_years", 0),
            "Career Progress": exp.get("career_progression_label", "N/A"),
            "Publications": res.get("total_publications", 0),
            "Journal Papers": res.get("journal_count", 0),
            "Strengths": summ.get("strength_count", 0),
            "Concerns": summ.get("concern_count", 0),
        })

    df = pd.DataFrame(comp_data)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Comparison charts
    col1, col2 = st.columns(2)
    with col1:
        fig = px.bar(df, x="Name", y="Publications",
                     title="Publications Comparison",
                     color="Publications", color_continuous_scale="Viridis")
        fig.update_layout(height=350)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.bar(df, x="Name", y="Total Exp (yrs)",
                     title="Experience Comparison",
                     color="Total Exp (yrs)", color_continuous_scale="Oranges")
        fig.update_layout(height=350)
        st.plotly_chart(fig, use_container_width=True)

    # Radar chart
    if len(results) >= 2:
        categories = ["Publications", "Journal Papers", "Total Exp (yrs)", "Strengths"]
        fig = go.Figure()
        for _, row in df.iterrows():
            values = [row[c] if isinstance(row[c], (int, float)) else 0 for c in categories]
            values.append(values[0])
            fig.add_trace(go.Scatterpolar(
                r=values,
                theta=categories + [categories[0]],
                fill='toself',
                name=row["Name"]
            ))
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True)),
            title="Candidate Profile Comparison",
            height=400,
        )
        st.plotly_chart(fig, use_container_width=True)


# MAIN APPLICATION
st.markdown('<p class="main-header">TALASH</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="sub-header">'
    'Talent Acquisition & Learning Automation for Smart Hiring - Milestone 2'
    '</p>',
    unsafe_allow_html=True
)
st.markdown("***")

# Initialize session state
if "results" not in st.session_state:
    st.session_state.results = []

# Sidebar: Input Controls
with st.sidebar:
    st.markdown("### CV Input")
    mode = st.radio(
        "Input mode",
        ["Upload CV(s)", "Load from folder"],
        key="input_mode"
    )

    if mode == "Upload CV(s)":
        uploaded_files = st.file_uploader(
            "Upload CV(s) - PDF",
            type=["pdf"],
            accept_multiple_files=True,
            key="upload_cvs"
        )
        if uploaded_files and st.button("Process Uploaded CVs", type="primary"):
            temp_paths = []
            for uf in uploaded_files:
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
                tmp.write(uf.read())
                tmp.close()
                temp_paths.append(Path(tmp.name))
            st.session_state.results = process_batch(temp_paths)
            for p in temp_paths:
                p.unlink(missing_ok=True)
            st.rerun()

    else:
        pdf_files = sorted(INPUT_DIR.glob("*.pdf")) if INPUT_DIR.exists() else []
        if pdf_files:
            st.write(f"Found **{len(pdf_files)}** CV(s) in folder")
            for f in pdf_files:
                st.caption(f"{f.name}")
            if st.button("Process All CVs", type="primary"):
                st.session_state.results = process_batch(pdf_files)
                st.rerun()
        else:
            st.warning("No PDFs found in `data/input_cvs/`")

    st.markdown("***")
    if st.session_state.results:
        st.success(f"{len(st.session_state.results)} CV(s) processed")
        if st.button("Clear Results"):
            st.session_state.results = []
            st.rerun()

# Main Content
results = st.session_state.results

if not results:
    st.markdown(
        """
        ### Welcome to TALASH
        Upload CVs or load from the `data/input_cvs/` folder to begin analysis.

        **This system will:**
        * Parse and extract structured information from CVs
        * Analyze educational profiles with CGPA normalization & gap detection
        * Analyze professional experience with timeline consistency checks
        * Evaluate research publications and authorship roles
        * Detect missing information and draft personalized follow-up emails
        * Compare candidates side-by-side with charts and metrics
        """
    )
else:
    # Dashboard overview
    render_metric_cards(results)
    st.markdown("***")

    # Candidate selector + tabs
    if len(results) == 1:
        selected_idx = 0
    else:
        candidate_names = [
            r["profile"].get("personal_information", {}).get("name", r["filename"])
            for r in results
        ]
        selected = st.selectbox("🔍 Select Candidate", candidate_names, key="candidate_select")
        selected_idx = candidate_names.index(selected)

    result = results[selected_idx]

    tabs = st.tabs([
        "Summary",
        "Education",
        "Experience",
        "Research",
        "Missing Info & Email",
        "Compare All",
        "Raw Data",
    ])

    with tabs[0]:
        render_summary_tab(result)
    with tabs[1]:
        render_education_tab(result)
    with tabs[2]:
        render_experience_tab(result)
    with tabs[3]:
        render_research_tab(result)
    with tabs[4]:
        render_email_tab(result)
    with tabs[5]:
        render_comparison_tab(results)
    with tabs[6]:
        st.subheader("Raw Parsed Data")
        st.json(result["profile"])
        with st.expander("Raw CV Text"):
            st.text(result["raw_text"][:5000])