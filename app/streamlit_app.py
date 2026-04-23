import json
import tempfile
from pathlib import Path

import streamlit as st
import pandas as pd

from preprocessing.pdf_reader import extract_text_from_pdf
from preprocessing.parser import parse_candidate_profile

# SAFE IMPORTS
import analysis.education_analysis as edu
import analysis.experience_analysis as exp
import analysis.research_analysis as res

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

    # ===== ANALYSIS (RUN ONCE ONLY) =====
    education = {}
    if hasattr(edu, "education_analysis"):
        education = edu.education_analysis(profile)
    elif hasattr(edu, "analyze_education_profile"):
        education = edu.analyze_education_profile(profile)

    experience = exp.analyze_experience(profile)
    research = res.research_analysis(profile)

    # =============================
    # TAB 2 — PARSED DATA
    # =============================
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

    # =============================
    # TAB 3 — ANALYSIS
    # =============================
    with tab3:
        st.subheader("Analysis")

        st.write("Education Analysis:")
        st.write(education)

        st.write("Experience Analysis:")
        st.write(experience)

        st.write("Research Analysis:")
        st.write(research)

    # =============================
    # TAB 4 — TABLES
    # =============================
    with tab4:
        st.subheader("Tables")

        if profile.get("education"):
            df = pd.DataFrame(profile["education"])
            st.dataframe(df)
        else:
            st.info("No education data")

    # =============================
    # TAB 5 — CHARTS
    # =============================
    with tab5:
        st.subheader("Publications by Year")

        if research.get("publications_by_year"):
            chart_df = pd.DataFrame.from_dict(
                research["publications_by_year"],
                orient="index",
                columns=["Publications"]
            )
            st.bar_chart(chart_df)
        else:
            st.info("No publication data available")

    # =============================
    # TAB 6 — EMAIL
    # =============================
    with tab6:
        st.subheader("Email Draft")

        st.write("Subject: CV Review Summary")
        st.write("Body: Candidate has been analyzed successfully.")

    # =============================
    # TAB 7 — COMPARE
    # =============================
    with tab7:
        st.subheader("Comparison")

        comparison = [{
            "name": profile.get("personal_information", {}).get("name", "Unknown"),
            "publications": research.get("total_publications", 0)
        }]

        df = pd.DataFrame(comparison)
        st.dataframe(df)


# =============================
# TAB 1 — UPLOAD
# =============================
with tab1:

    st.title("TALASH - Smart CV Analyzer")
    st.markdown("### Milestone 2 Integrated System")

    mode = st.radio(
        "Choose input source",
        ["Upload CV (PDF)", "Load sample CV from folder"],
        horizontal=True,
        key="input_mode"
    )

    if mode == "Upload CV (PDF)":
        uploaded_file = st.file_uploader(
            "Upload CV (PDF)",
            type=["pdf"],
            key="upload_cv"
        )

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
            st.warning("No sample PDFs found")
        else:
            selected_pdf = st.selectbox(
                "Select a sample CV",
                options=pdf_files,
                format_func=lambda p: p.name,
            )

            if st.button("Process Selected CV"):
                text, profile = process_pdf(selected_pdf)
                render_profile(text, profile)