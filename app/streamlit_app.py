import json
import tempfile
from pathlib import Path

import streamlit as st

from preprocessing.pdf_reader import extract_text_from_pdf
from preprocessing.parser import parse_candidate_profile

st.set_page_config(page_title="TALASH - CV Analyzer", layout="wide")

INPUT_DIR = Path("data/input_cvs")


def process_pdf(pdf_path: Path) -> tuple[str, dict]:
    text = extract_text_from_pdf(pdf_path)
    profile = parse_candidate_profile(text)
    return text, profile


def render_profile(text: str, profile: dict) -> None:
    st.success("CV processed successfully")

    st.divider()

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

    st.divider()

    with st.expander("Raw Extracted Text"):
        st.text(text[:6000] if text else "No text extracted")

    with st.expander("Parsed JSON Output"):
        st.code(json.dumps(profile, indent=2), language="json")


st.title("TALASH - Smart CV Analyzer")
st.markdown("### Milestone 1 Prototype")

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