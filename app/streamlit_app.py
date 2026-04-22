import json
import tempfile
from pathlib import Path

import streamlit as st

from preprocessing.pdf_reader import extract_text_from_pdf
from preprocessing.parser import parse_candidate_profile

# =============================
# PAGE CONFIG (MUST BE FIRST)
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
def process_pdf(pdf_path: Path) -> tuple[str, dict]:
    text = extract_text_from_pdf(pdf_path)
    profile = parse_candidate_profile(text)
    return text, profile

# =============================
# RENDER PROFILE (UPDATED)
# =============================
def render_profile(text: str, profile: dict) -> None:

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

        with st.expander("Raw Extracted Text"):
            st.text(text[:6000] if text else "No text extracted")

        with st.expander("Parsed JSON Output"):
            st.code(json.dumps(profile, indent=2), language="json")

    # -------- TAB 3: Analysis --------
    with tab3:
        st.subheader("Analysis (Milestone 2)")
        st.info("Education, Experience, Research, and Summary will appear here")

    # -------- TAB 4: Tables --------
    with tab4:
        st.subheader("Tables")

        if profile.get("education"):
            import pandas as pd
            df = pd.DataFrame(profile["education"])
            st.dataframe(df)
        else:
            st.info("No education data available")

    # -------- TAB 5: Charts --------
    with tab5:
        st.subheader("Charts")
        st.info("Charts will be displayed here")

    # -------- TAB 6: Email Draft --------
    with tab6:
        st.subheader("Email Draft")
        st.info("Email draft will be generated here")

    # -------- TAB 7: Compare --------
    with tab7:
        st.subheader("Candidate Comparison")
        st.info("Comparison feature coming soon")


# =============================
# TAB 1: UPLOAD UI (MAIN)
# =============================
with tab1:

    st.title("TALASH - Smart CV Analyzer")
    st.markdown("### Milestone 2 UI Prototype")

    mode = st.radio(
        "Choose input source",
        ["Upload CV (PDF)", "Load sample CV from folder"],
        horizontal=True,
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