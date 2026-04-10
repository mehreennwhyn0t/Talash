# TALASH – Smart CV Analyzer

## Project Overview

TALASH is a CV analysis system that extracts structured information from PDF resumes.
It processes raw CV text and converts it into a structured JSON format for analysis.

The system demonstrates:

* PDF text extraction
* Information parsing
* JSON generation
* Interactive UI using Streamlit

---

## Features

* Upload CV (PDF)
* Load sample CV from folder
* Extract:

  * Personal Information
  * Skills
  * Education
  * Experience
  * Publications
* Detect missing information
* View raw extracted text
* Generate structured JSON output

---

## Project Structure

```
Talash/
│
├── app/
│   └── streamlit_app.py
│
├── preprocessing/
│   ├── pdf_reader.py
│   └── parser.py
│
├── data/
│   ├── input_cvs/
│   └── sample_outputs/
│
├── docs/
│   ├── architecture_diagram.png
│   ├── data_flow_diagram.png
│   ├── wireframe_upload.png
│   ├── wireframe_dashboard.png
│   ├── wireframe_results.png
│   └── screenshots/
│
├── requirements.txt
└── README.md
```

---

## How to Run

### Install dependencies

```
pip install -r requirements.txt
```

### Run the application

```
streamlit run app/streamlit_app.py
```

### Open in browser

```
http://localhost:8501
```

---

## System Workflow

1. User uploads or selects a CV
2. PDF text is extracted
3. Parser processes the text
4. Structured JSON is generated
5. Missing fields are flagged
6. Results are displayed in the UI

---

## Technologies Used

* Python
* Streamlit
* PDF processing libraries
* Regular expressions
* JSON handling

---

## Limitations

* Works best with structured CVs
* Some fields may not be detected if formatting is inconsistent
* Publications extraction depends on CV format

---

## Future Improvements

* NLP-based parsing
* Improved publications extraction
* CV scoring system
* Job matching functionality
* Deployment as a web application

---

## Milestone 1 Status

* UI prototype completed
* CV upload and folder input implemented
* Parsing system implemented
* JSON output generated
* Documentation and screenshots included in docs folder

---

## Conclusion

TALASH provides a functional prototype for CV parsing with structured output and a simple interface, serving as a foundation for future development.

---
