import json
import tempfile
from pathlib import Path

import streamlit as st

from preprocessing.pdf_reader import extract_text_from_pdf
from preprocessing.parser import parse_candidate_profile

st.set_page_config(page_title="TALASH - CV Analyzer", layout="wide")

st.title("TALASH - Smart CV Analyzer")
st.markdown("### Milestone 1 Prototype")

uploaded_file = st.file_uploader("Upload CV (PDF)", type=["pdf"])

if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(uploaded_file.read())
        temp_pdf_path = tmp_file.name

    try:
        text = extract_text_from_pdf(temp_pdf_path)
        profile = parse_candidate_profile(text)

        st.success("CV processed successfully")

        st.divider()

        st.subheader("Personal Information")
        st.json(profile.get("personal_information", {}))

        st.subheader("Skills")
        st.write(", ".join(profile.get("skills", [])))

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Education")
            st.json(profile.get("education", []))

        with col2:
            st.subheader("Experience")
            st.json(profile.get("experience", []))

        st.divider()

        with st.expander("Raw Extracted Text"):
            st.text(text[:4000])

        with st.expander("Parsed JSON Output"):
            st.code(json.dumps(profile, indent=2), language="json")

    except Exception as e:
        st.error(f"Error: {e}")

    finally:
        Path(temp_pdf_path).unlink(missing_ok=True)

else:
    st.info("Upload a CV to begin.")
