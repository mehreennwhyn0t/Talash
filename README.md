# TALASH – AI-Powered Smart HR Recruitment System

**CS 417 – Large Language Models | Spring 2026 | SEECS, NUST**  
Mehreen Raheel · Eeshal Tahir · Huma Ejaz

---

## Overview

TALASH is a fully integrated AI-powered recruitment intelligence platform that analyzes candidate CVs end-to-end. It extracts structured profiles from PDF resumes using Google Gemini (with regex fallback), runs nine analysis modules covering education, experience, research, skills, and more, and presents results through an interactive 8-tab Streamlit web application.

---

## Features

### CV Ingestion & Parsing
- Batch PDF processing from a folder with a progress bar
- LLM-enhanced structured extraction via Google Gemini (`gemini-2.0-flash`)
- Regex fallback parser for environments without an API key
- Handles diverse CV formats across different career stages and academic backgrounds

### Analysis Modules
| Module | What it does |
|---|---|
| **Education Analysis** | CGPA/percentage normalization, institution quality (4-tier QS lookup), gap detection, progression trend, level classification (SSC → PhD) |
| **Experience Analysis** | Timeline normalization, overlap & gap detection with severity classification, career progression assessment |
| **Research Analysis** | Journal ranking lookup (IF, Scopus/WoS, Q1–Q4) and conference ranking lookup (CORE A*–C), authorship role detection, research quality score |
| **Topic Variability** | 6-domain keyword classification (ML/AI, Healthcare, Education, Cybersecurity, Data Science, Software Engineering) with diversity score |
| **Co-Author Analysis** | Collaboration network from publication author lists, top-10 collaborator table, collaboration score |
| **Supervision / Books / Patents** | MS/PhD supervision with role distinction, book records with ISBN extraction, patents with patent number extraction |
| **Skill Alignment** | 25-domain keyword taxonomy, 4-tier evidence classification (Strongly/Partially/Weakly Evidenced, Unsupported) across 6 evidence sources |
| **Missing Info & Email** | Three-tier missing field classification, Gemini-generated personalized outreach email per candidate |
| **Candidate Summary** | Rule-based suitability label + LLM-generated narrative summary |

### Ranking Module *(Extra Credit)*
Weighted composite score across all 7 analysis dimensions:
- Education 20% · Experience 20% · Research 25% · Topic Diversity 5% · Co-Author 5% · Supervision/IP 10% · Skill Alignment 15%

Outputs a ranked leaderboard DataFrame with per-candidate score justification.

### Web Application
8-tab Streamlit interface:
1. **Summary** – Suitability label and LLM narrative
2. **Education** – Degree records, institution quality, gap analysis, score chart
3. **Experience** – Timeline, overlaps, gaps, career progression
4. **Research** – Enriched publication table (indexing, quartile, IF, authorship), topic breakdown, co-author table, SBP analysis
5. **Skill Alignment** – 25-domain evidence breakdown
6. **Missing Info & Email** – Flagged fields and personalized email draft
7. **Compare All & Ranking** – Multi-candidate comparison table, radar chart, ranked leaderboard
8. **Raw Data** – Full parsed JSON viewer

---

## Project Structure

```
Talash/
├── app/
│   └── streamlit_app.py          # 8-tab Streamlit application
│
├── analysis/
│   ├── education_analysis.py     # Education profile analysis
│   ├── experience_analysis.py    # Experience & employment history
│   ├── research_analysis.py      # Research profile with ranking lookups
│   ├── topic_analysis.py         # Topic variability analysis
│   ├── coauthor_analysis.py      # Co-author network analysis
│   ├── supervision_books_patents.py  # SBP module
│   ├── skill_alignment.py        # 25-domain skill evidence analysis
│   ├── ranking_module.py         # Weighted composite ranking
│   ├── summary_generator.py      # Suitability label + LLM narrative
│   ├── email_drafter.py          # Missing info detection + email drafting
│   └── normalizers.py            # Shared normalization utilities
│
├── preprocessing/
│   ├── pdf_reader.py             # pdfplumber-based PDF extraction
│   └── parser.py                 # Gemini LLM + regex fallback parser
│
├── llm/                          # Gemini API integration
│
├── data/
│   ├── input_cvs/                # Place CV PDFs here for batch processing
│   ├── lookup/
│   │   ├── journal_rankings.csv  # IF, Scopus/WoS indexing, Q1–Q4 quartile
│   │   └── conference_rankings.csv  # CORE rank (A*, A, B, C)
│   └── sample_outputs/
│
├── docs/                         # Architecture diagrams and screenshots
├── requirements.txt
└── README.md
```

---

## Setup & Running

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Gemini API key

Create a `.env` file in the project root:

```
GEMINI_API_KEY=your_api_key_here
```

Without a key the system falls back to the regex parser and generates rule-based summaries — all analysis modules still run normally.

### 3. Run the application

```bash
streamlit run app/streamlit_app.py
```

Then open `http://localhost:8501` in your browser.

### 4. Add CVs

Drop PDF CVs into `data/input_cvs/` and use the **Load from Folder** option in the app, or upload files directly through the browser interface.

---

## Technologies

| Technology | Version | Purpose |
|---|---|---|
| Python | 3.11+ | Core language |
| Google Gemini | gemini-2.0-flash | LLM parsing & email drafting |
| pdfplumber | 0.11+ | PDF text extraction |
| Streamlit | 1.33+ | Web application |
| Plotly | 5.x | Interactive charts (bar, pie, radar) |
| Pandas | 2.x | Data processing & ranking |
| python-dotenv | 1.0+ | API key management |

---

## Limitations

- Journal and conference ranking lookups use curated static CSVs. Venues not present in the lookup return "Unknown" for indexing and quartile.
- Topic classification uses keyword matching and may misclassify interdisciplinary publications with non-standard terminology.
- Co-author detection depends on the parser correctly extracting structured author lists from the CV.
- The Gemini API key is required for LLM-enhanced parsing and email generation; without it, the regex fallback is used.

---

## Milestones

| Milestone | Scope |
|---|---|
| M1 | CV upload, PDF extraction, basic parsing, JSON output, Streamlit prototype |
| M2 | LLM parsing, education & experience analysis, partial research, missing info detection, 7-tab app |
| M3 | Full research analysis with ranking lookups, topic variability, co-author, SBP, skill alignment, ranking module (extra credit), complete 8-tab app, CV generalization |
