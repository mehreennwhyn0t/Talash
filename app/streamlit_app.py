import json
import tempfile
from pathlib import Path

import streamlit as st
import pandas as pd

from preprocessing.pdf_reader import extract_text_from_pdf
from preprocessing.parser import parse_candidate_profile

# SAFE MODULE IMPORTS
import analysis.education_analysis as edu
import analysis.experience_analysis as exp
import analysis.research_analysis as res
import analysis.summary_generator as summ

# =============================
# PAGE CONFIG
# =============================
st.set_page_config(page_title="TALASH - CV Analyzer", layout="wide")

# =============================
# TABS
# =============================
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "Upload",
    "Parsed Data",
    "Analysis",
    "Tables",
    "Charts",
    "Email Drafts",
    "Compare"
])

INPUT_DIR = Path("data/input_cvs")

# =============================
# PROCESS PDF
# =============================
def process_pdf(pdf_path: Path):
    text = extract_text_from_pdf(pdf_path)
    profile = parse_candidate_profile(text)
    return text, profile


# =============================
# RENDER PROFILE
# =============================
def render_profile(text: str, profile: dict):

    # SAFE ANALYSIS CALLS
    education = {}
    if hasattr(edu, "analyze_education_profile"):
        education = edu.analyze_education_profile(profile)
    elif hasattr(edu, "education_analysis"):
        education = edu.education_analysis(profile)

    experience = {}
    if hasattr(exp, "analyze_experience_profile"):
        experience = exp.analyze_experience_profile(profile)
    elif hasattr(exp, "experience_analysis"):
        experience = exp.experience_analysis(profile)

    research = {}
    if hasattr(res, "analyze_research_profile"):
        research = res.analyze_research_profile(profile)
    elif hasattr(res, "research_analysis"):
        research = res.research_analysis(profile)

    summary = {}
    if hasattr(summ, "generate_summary"):
        summary = summ.generate_summary(education, experience, research, {})

    # -------- TAB 2: Parsed Data --------
    with tab2:
        st.success("CV processed successfully")

        st.subheader("Personal Information")
        st.json(profile.get("personal_information", {}))

        st.subheader("Skills")
        skills = profile.get("skills", [])
        st.write(", ".join(skills) if skills else "No skills detected")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Education")
            st.json(profile.get("education", []))

        with col2:
            st.subheader("Experience")
            st.json(profile.get("experience", []))

        st.subheader("Publications")
        st.json(profile.get("publications", []))

        st.subheader("Missing Information Flags")
        st.write(profile.get("missing_information", []))

    # -------- TAB 3: Analysis --------
    with tab3:
        st.subheader("Education Analysis")

        if isinstance(education, dict):
            st.write("Progression:", education.get("progression_label", "N/A"))
            st.write("Consistency:", education.get("specialization_consistency", "N/A"))
            st.write("Summary:", education.get("education_summary", "N/A"))
        else:
            st.info("No education analysis available")

        st.divider()

        st.subheader("Experience Analysis")
        st.write(experience if experience else "No experience data")

        st.divider()

        st.subheader("Research Analysis")
        st.write(research if research else "No research data")

        st.divider()

        st.subheader("Candidate Summary")
        st.write(summary if summary else "No summary generated")

    # -------- TAB 4: Tables --------
    with tab4:
        st.subheader("Education Table")

        if isinstance(education, dict) and education.get("education_table"):
            df = pd.DataFrame(education["education_table"])
            st.dataframe(df)
        else:
            st.info("No structured education data")

        st.subheader("Normalized Scores")

        if isinstance(education, dict) and education.get("normalized_scores"):
            df2 = pd.DataFrame(education["normalized_scores"])
            st.dataframe(df2)

    # -------- TAB 5: Charts --------
    with tab5:
        st.subheader("Publications by Year")

        if isinstance(research, dict) and research.get("publications_by_year"):
            chart_data = pd.DataFrame.from_dict(
                research["publications_by_year"],
                orient="index",
                columns=["Publications"]
            )
            st.bar_chart(chart_data)
        else:
            st.info("No publication data available")

    # -------- TAB 6: Email Draft --------
    with tab6:
        st.subheader("Email Draft")

        if isinstance(summary, dict) and summary.get("email_draft"):
            st.write("Subject:")
            st.code(summary["email_draft"].get("subject", ""))

            st.write("Body:")
            st.write(summary["email_draft"].get("body", ""))
        else:
            st.info("Email draft not available yet")

    # -------- TAB 7: Compare --------
    with tab7:
        st.subheader("Candidate Comparison")

        if isinstance(research, dict):
            st.write("Publications:", research.get("total_publications", 0))

        if isinstance(education, dict):
            st.write("Progression:", education.get("progression_label", "N/A"))
# =============================
# TAB 1: UPLOAD UI
# =============================
with tab1:

    st.title("TALASH - Smart CV Analyzer")
    st.markdown("### Milestone 2 Integrated System")

    mode = st.radio(
        "Choose input source",
        ["Upload CV (PDF)", "Load sample CV from folder"],
        horizontal=True,
        key="main_radio"   # ✅ FIXED DUPLICATE ERROR
    )

    if mode == "Upload CV (PDF)":
        uploaded_file = st.file_uploader("Upload CV (PDF)", type=["pdf"])

        if uploaded_file:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(uploaded_file.read())
                temp_pdf_path = Path(tmp_file.name)

            try:
                text, profile = process_pdf(temp_pdf_path)
                render_profile(text, profile)
            except Exception as e:
                st.error(f"Error: {e}")
            finally:
                temp_pdf_path.unlink(missing_ok=True)
        else:
            st.info("Upload a CV to begin.")

    else:
        pdf_files = sorted(INPUT_DIR.glob("*.pdf")) if INPUT_DIR.exists() else []

        if not pdf_files:
            st.warning("No sample PDFs found in data/input_cvs/")
        else:
            selected_pdf = st.selectbox(
                "Select a sample CV from data/input_cvs/",
                options=pdf_files,
                format_func=lambda p: p.name,
            )

            if st.button("Process Selected CV"):
                try:
                    text, profile = process_pdf(selected_pdf)
                    render_profile(text, profile)
                except Exception as e:
                    st.error(f"Error: {e}")