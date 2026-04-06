import json
import tempfile
from pathlib import Path

import streamlit as st

from preprocessing.pdf_reader import extract_text_from_pdf
from preprocessing.parser import parse_candidate_profile

st.set_page_config(page_title="TALASH - Milestone 1", layout="wide")

st.title("TALASH - CV Parser Prototype")
st.markdown("**Milestone 1 Early Prototype**")
st.write("Upload a CV PDF to extract baseline candidate information.")

uploaded_file = st.file_uploader("Upload CV (PDF)", type=["pdf"])

if uploaded_file is not None:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(uploaded_file.read())
        temp_pdf_path = tmp_file.name

    try:
        extracted_text = extract_text_from_pdf(temp_pdf_path)
        parsed_profile = parse_candidate_profile(extracted_text)

        st.success("CV processed successfully.")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Personal Information")
            st.json(parsed_profile.get("personal_information", {}))

            st.subheader("Skills")
            st.write(parsed_profile.get("skills", []))

        with col2:
            st.subheader("Education")
            st.json(parsed_profile.get("education", []))

            st.subheader("Experience")
            st.json(parsed_profile.get("experience", []))

        with st.expander("Show Extracted Text"):
            st.text(extracted_text[:4000] if extracted_text else "No text extracted.")

        with st.expander("Show Raw Parsed JSON"):
            st.code(json.dumps(parsed_profile, indent=2), language="json")

    except Exception as error:
        st.error(f"Error processing PDF: {error}")

    finally:
        temp_path = Path(temp_pdf_path)
        if temp_path.exists():
            temp_path.unlink()
else:
    st.info("Please upload a PDF CV to begin.")
