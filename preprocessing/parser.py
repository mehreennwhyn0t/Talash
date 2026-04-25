"""
parser.py

CV parser with LLM-enhanced extraction + regex fallback.
Uses Gemini API for intelligent extraction when available.
Falls back to regex-based parsing for robustness.
"""

import re
import json
from pathlib import Path

# Regex patterns (fallback)
EMAIL_RE    = re.compile(r'[\w\.\-\+]+@[\w\.\-]+\.\w{2,}')
PHONE_RE    = re.compile(r'(\+92[\s\-]?\d{3}[\s\-]?\d{7}|\+\d{1,3}[\s\-]?\d{6,12}|0\d{3}[\s\-]?\d{7})')
YEAR_RE     = re.compile(r"\b((?:19|20)\d{2})\b")
DURATION_RE = re.compile(
    r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[\-\s]\d{4}\s*[-–]\s*'
    r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[\-\s]\d{4}|'
    r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[\-\s]\d{4}\s*[-–]\s*Present',
    re.I
)

DEGREE_KEYWORDS = [
    "phd", "ph.d", "doctorate", "ms ", "msc", "m.sc", "mphil", "m.phil",
    "masters", "master of", "be ", "b.e", "bsc", "b.sc", "bs ", "b.s",
    "bachelor", "hssc", "fsc", "f.sc", "pre-engineering", "pre engineering",
    "ssc", "matric", "intermediate", "a-levels", "o-levels"
]

JOB_KEYWORDS = [
    "professor", "lecturer", "engineer", "manager", "director", "coordinator",
    "researcher", "analyst", "developer", "consultant", "officer", "assistant",
    "associate", "head", "dean", "principal", "supervisor", "instructor",
    "scientist", "specialist", "advisor", "architect", "lead"
]


# LLM-based parsing
def parse_with_llm(raw_text: str) -> dict:
    """
    Use Gemini to extract structured profile from raw CV text.
    Returns parsed profile dict or None on failure.
    """
    try:
        from llm.gemini_client import call_gemini, is_api_available
        from llm.prompts import cv_parsing_prompt

        if not is_api_available():
            return None

        prompt = cv_parsing_prompt(raw_text)
        result = call_gemini(prompt, expect_json=True)

        if isinstance(result, dict) and not result.get("parse_error"):
            # Ensure all required keys exist
            defaults = {
                "personal_information": {},
                "education": [],
                "experience": [],
                "publications": [],
                "skills": [],
                "supervision": [],
                "books": [],
                "patents": [],
                "certifications": [],
                "awards": [],
            }
            for key, default in defaults.items():
                if key not in result:
                    result[key] = default
            return result

    except Exception as e:
        print(f"[TALASH] LLM parsing failed: {e}")

    return None


# Section splitter (regex fallback)
def split_into_sections(lines):
    """Splits raw CV lines into named sections based on header keywords."""
    SECTION_MARKERS = {
        "education":     ["education"],
        "experience":    ["civil experience", "professional experience",
                          "work experience", "employment history"],
        "publications":  ["publications", "research publications"],
        "skills":        ["skills", "technical skills", "competencies", "expertise"],
        "references":    ["references"],
        "awards":        ["awards", "scholarships", "achievements"],
        "qualifications":["professional qualification"],
    }

    sections = {"header": []}
    current = "header"

    for line in lines:
        lower = line.lower().strip()
        matched = False
        for section, markers in SECTION_MARKERS.items():
            if any(lower == m or lower.startswith(m) for m in markers):
                current = section
                matched = True
                break
        if not matched:
            sections.setdefault(current, []).append(line)

    return sections


# Personal information (regex fallback)
def extract_personal_information(header_lines, full_text):
    info = {"name": "", "email": "", "phone": "", "position_applied": "", "dob": ""}

    full = "\n".join(header_lines)

    # Position applied
    pos_m = re.search(r'Candidate for the Post of (.+?)(?:\(Apply Date|$)', full, re.I)
    if pos_m:
        info["position_applied"] = pos_m.group(1).strip()

    # Name
    name_m = re.search(
        r'\bName\s+([A-Za-z][A-Za-z\s\.]{2,60}?)\s+(?:Father|Guardian|Date/Place)',
        full, re.I
    )
    if name_m:
        info["name"] = name_m.group(1).strip().title()
    else:
        for i, line in enumerate(header_lines):
            if "Candidate for the Post" in line:
                for j in range(i + 1, min(i + 5, len(header_lines))):
                    candidate = header_lines[j].strip()
                    name_part = re.sub(r"Father.*", "", candidate, flags=re.I).strip()
                    name_part = re.sub(r"^Name\s*", "", name_part, flags=re.I).strip()
                    if name_part and re.match(r'^[A-Za-z\s\.]+$', name_part) and len(name_part) > 3:
                        info["name"] = name_part.title()
                        break
                break

    # DOB
    dob_m = re.search(r'Date/Place of\s*Birth:\s*([\d\-A-Za-z]+)', full, re.I)
    if dob_m:
        info["dob"] = dob_m.group(1).strip()

    # Email and phone
    ref_idx = full_text.lower().find("references")
    search_text = full_text[:ref_idx] if ref_idx > 200 else full_text

    email_m = EMAIL_RE.search(search_text)
    if email_m:
        info["email"] = email_m.group(0)

    phone_m = PHONE_RE.search(search_text)
    if phone_m:
        info["phone"] = phone_m.group(0).strip()

    return info


# Education (regex fallback)
def extract_education(edu_lines):
    entries = []
    data_lines = [
        l for l in edu_lines if l.strip()
        and not re.match(r'^Name of Degree', l, re.I)
        and not re.match(r'^(Grade|Specialization|Passing|Board)', l, re.I)
    ]

    for line in data_lines:
        stripped = line.strip()
        if not stripped:
            continue
        lower = stripped.lower()
        if not any(kw in lower for kw in DEGREE_KEYWORDS):
            continue

        years = YEAR_RE.findall(stripped)
        year = years[-1] if years else ""

        grade_m = re.search(r'\b(\d{1,3}\.?\d{0,2})\s*(%|\/\s*\d+\.?\d*)?', stripped)
        grade = grade_m.group(0).strip() if grade_m else ""

        after_year = ""
        if year:
            year_idx = stripped.rfind(year)
            after_year = stripped[year_idx + len(year):].strip()

        degree_raw = stripped
        if grade:
            grade_idx = stripped.find(grade)
            degree_raw = stripped[:grade_idx].strip() if grade_idx > 5 else stripped

        degree = re.sub(r'\s{2,}.*', '', degree_raw).strip()

        entries.append({
            "degree": degree,
            "grade": grade,
            "year": year,
            "institution": after_year if after_year else "",
            "specialization": "",
            "start_year": "",
            "end_year": year,
            "grade_type": ""
        })

    return entries[:20]


# Experience (regex fallback)
def extract_experience(exp_lines):
    entries = []
    data_lines = [
        l for l in exp_lines if l.strip()
        and not re.match(r'^Name of Post', l, re.I)
        and not re.match(r'^(Organization|Location|Duration)', l, re.I)
    ]

    for line in data_lines:
        stripped = line.strip()
        if not stripped:
            continue
        lower = stripped.lower()
        if not any(kw in lower for kw in JOB_KEYWORDS):
            continue

        dur_m = DURATION_RE.search(stripped)
        duration = dur_m.group(0).strip() if dur_m else ""

        years = YEAR_RE.findall(duration) if duration else YEAR_RE.findall(stripped)
        start_year = years[0] if len(years) > 0 else ""
        end_year = years[1] if len(years) > 1 else (
            "Present" if "present" in stripped.lower() else ""
        )

        title_part = stripped
        if dur_m:
            title_part = stripped[:dur_m.start()].strip()

        title = ""
        organization = ""
        for kw in JOB_KEYWORDS:
            kw_m = re.search(r'\b' + kw + r'\b', title_part, re.I)
            if kw_m:
                end_of_title = kw_m.end()
                title = title_part[:end_of_title].strip()
                organization = title_part[end_of_title:].strip().lstrip(',').strip()
                break
        if not title:
            title = title_part

        entries.append({
            "title": title,
            "organization": organization,
            "start_year": start_year,
            "end_year": end_year,
            "start_date": "",
            "end_date": "",
            "duration": duration,
            "location": "",
            "employment_type": "",
            "responsibilities": ""
        })

    return entries[:20]


# Publications (regex fallback)
def extract_publications(pub_lines):
    entries = []
    data_lines = [
        l for l in pub_lines if l.strip()
        and not re.match(r'^Paper Title', l, re.I)
        and not re.match(r'^(Name of Author|Name of CO|Published|Impact|Factor|No\b)', l, re.I)
    ]

    current_title_parts = []
    current_venue = ""
    current_type = ""
    current_year = ""
    current_impact = ""

    def flush(parts, venue, pub_type, year, impact):
        if parts:
            title = " ".join(parts).strip()
            title = re.sub(r'\s+', ' ', title)
            entries.append({
                "title": title,
                "venue": venue,
                "type": pub_type,
                "year": year,
                "impact_factor": impact,
                "authors": [],
                "candidate_position": "unknown"
            })

    for line in data_lines:
        stripped = line.strip()
        if not stripped:
            continue

        if re.search(r'\b(Journal|Conference|Workshop|Symposium|Proceedings)\b', stripped, re.I):
            venue_m = re.search(
                r'(International Journal|Journal|International Conference|Conference|Workshop|Symposium)',
                stripped, re.I
            )
            current_venue = venue_m.group(0) if venue_m else ""
            current_type = "journal" if "journal" in current_venue.lower() else "conference"
            impact_m = re.search(r'\b(\d+\.\d{2})\b', stripped)
            current_impact = impact_m.group(0) if impact_m else ""
            years = YEAR_RE.findall(stripped)
            current_year = years[-1] if years else ""
            flush(current_title_parts, current_venue, current_type, current_year, current_impact)
            current_title_parts = []
            current_venue = ""
            current_type = ""
            current_year = ""
            current_impact = ""
        else:
            if len(stripped.split()) >= 3:
                current_title_parts.append(stripped)

    flush(current_title_parts, current_venue, current_type, current_year, current_impact)
    return entries[:20]


# Skills (regex fallback)
def extract_skills(skills_lines, full_text):
    SKILL_KEYWORDS = [
        "Python", "Java", "C++", "C#", "MATLAB", "R", "SQL", "JavaScript",
        "Machine Learning", "Deep Learning", "NLP", "Natural Language Processing",
        "Computer Vision", "Data Analysis", "Data Science", "TensorFlow", "PyTorch",
        "Keras", "Scikit-learn", "Pandas", "NumPy", "Power Electronics",
        "Control Systems", "Embedded Systems", "IoT", "Wireless Communication",
        "Signal Processing", "5G", "OFDM", "NOMA", "Optimization",
        "Research", "Teaching", "Project Management", "Technical Writing",
        "LaTeX", "Git", "Docker", "Linux", "Cloud Computing", "AWS", "Azure",
        "Streamlit", "Flask", "Django",
    ]

    found = []
    section_text = " ".join(skills_lines)
    if len(section_text.strip()) > 20:
        for skill in SKILL_KEYWORDS:
            if re.search(r'\b' + re.escape(skill) + r'\b', section_text, re.I):
                found.append(skill)

    for skill in SKILL_KEYWORDS:
        if skill not in found and re.search(r'\b' + re.escape(skill) + r'\b', full_text, re.I):
            found.append(skill)

    return sorted(set(found))


# Missing information flags
def detect_missing(profile):
    missing = []
    pi = profile.get("personal_information", {})
    if not pi.get("email"):
        missing.append("Email address not found in CV")
    if not pi.get("phone"):
        missing.append("Phone number not found in CV")
    if not pi.get("dob"):
        missing.append("Date of birth not detected")
    if not profile.get("education"):
        missing.append("Education records not detected - check CV format")
    if not profile.get("experience"):
        missing.append("Work experience not detected - check CV format")
    if not profile.get("publications"):
        missing.append("No publications detected")

    for edu in profile.get("education", []):
        if not edu.get("grade"):
            missing.append(
                f"Grade/CGPA missing for: {edu.get('degree', 'unknown degree')}"
            )
            break

    return missing


# Main entry point
def parse_candidate_profile(text: str, use_llm: bool = True) -> dict:
    """
    Main parser. Accepts raw extracted text from a CV PDF.
    Uses LLM for intelligent extraction when available, with regex fallback.
    Returns a structured profile dict.
    """

    # Try LLM-based parsing first
    if use_llm:
        llm_result = parse_with_llm(text)
        if llm_result:
            llm_result["missing_information"] = detect_missing(llm_result)
            llm_result["_parsing_method"] = "llm"
            return llm_result

    # Fallback to regex-based parsing
    lines = text.splitlines()
    sections = split_into_sections(lines)
    full_text = text

    profile = {
        "personal_information": extract_personal_information(
            sections.get("header", []), full_text
        ),
        "education":    extract_education(sections.get("education", [])),
        "experience":   extract_experience(sections.get("experience", [])),
        "publications": extract_publications(sections.get("publications", [])),
        "skills":       extract_skills(sections.get("skills", []), full_text),
        "supervision":  [],
        "books":        [],
        "patents":      [],
        "certifications": [],
        "awards":       [],
    }

    profile["missing_information"] = detect_missing(profile)
    profile["_parsing_method"] = "regex"

    return profile
