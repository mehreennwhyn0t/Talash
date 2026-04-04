import re
from collections import OrderedDict

EMAIL_RE = re.compile(r'[\w\.-]+@[\w\.-]+\.\w+')
PHONE_RE = re.compile(r'(\+?\d[\d\-\s]{7,}\d)')
YEAR_RE = re.compile(r'(19|20)\d{2}')
CGPA_RE = re.compile(r'(cgpa|gpa)\s*[:\-]?\s*(\d+(\.\d+)?)', re.IGNORECASE)

SKILL_KEYWORDS = [
    "python",
    "java",
    "c++",
    "machine learning",
    "deep learning",
    "nlp",
    "data analysis",
    "sql",
    "streamlit",
    "pandas",
]

SECTION_LABELS = {
    "education": ["education", "academic background", "academics"],
    "experience": ["experience", "work experience", "employment", "work history"],
    "skills": ["skills", "technical skills", "competencies"],
    "publications": ["publications", "research papers", "articles"],
}

DEGREE_KEYWORDS = [
    "phd",
    "mphil",
    "ms",
    "msc",
    "bs",
    "bsc",
    "bachelor",
    "master",
    "intermediate",
    "hssc",
    "ssc",
    "matric",
]

JOB_HINTS = [
    "intern",
    "engineer",
    "developer",
    "analyst",
    "assistant",
    "manager",
    "officer",
    "lecturer",
    "teacher",
    "researcher",
]


def clean_lines(text: str) -> list:
    """
    Split text into non-empty stripped lines.
    """
    return [line.strip() for line in text.splitlines() if line.strip()]


def split_sections(text: str) -> dict:
    """
    Detect common CV sections using simple heading-based matching.
    Returns a dictionary of section_name -> section_text.
    """
    lower_text = text.lower()
    found_positions = {}

    for section_name, keywords in SECTION_LABELS.items():
        positions = [lower_text.find(keyword) for keyword in keywords if lower_text.find(keyword) != -1]
        if positions:
            found_positions[section_name] = min(positions)

    ordered_positions = OrderedDict(sorted(found_positions.items(), key=lambda item: item[1]))
    section_names = list(ordered_positions.keys())

    sections = {}
    for index, section_name in enumerate(section_names):
        start = ordered_positions[section_name]
        end = ordered_positions[section_names[index + 1]] if index + 1 < len(section_names) else len(text)
        sections[section_name] = text[start:end].strip()

    return sections


def extract_personal_information(text: str) -> dict:
    """
    Extract very basic personal information from the CV text.
    """
    lines = clean_lines(text)
    name = lines[0] if lines else "Unknown Candidate"

    email_match = EMAIL_RE.search(text)
    phone_match = PHONE_RE.search(text)

    return {
        "name": name[:100],
        "email": email_match.group(0) if email_match else "",
        "phone": phone_match.group(0) if phone_match else "",
    }


def extract_skills(text: str) -> list:
    """
    Detect a small set of common skills from the CV text using keyword matching.
    """
    lower_text = text.lower()
    found_skills = [skill.title() for skill in SKILL_KEYWORDS if skill in lower_text]
    return sorted(set(found_skills))


def extract_education(section_text: str) -> list:
    """
    Baseline education extraction using line-level heuristics.
    Returns a list of simple education records.
    """
    education_records = []
    lines = clean_lines(section_text)

    for line in lines:
        lower_line = line.lower()

        if any(keyword in lower_line for keyword in DEGREE_KEYWORDS):
            years = YEAR_RE.findall(line)
            cgpa_match = CGPA_RE.search(line)

            record = {
                "degree_text": line,
                "year_mentions": re.findall(r'(?:19|20)\d{2}', line),
                "cgpa": cgpa_match.group(2) if cgpa_match else "",
            }
            education_records.append(record)

    return education_records


def extract_experience(section_text: str) -> list:
    """
    Baseline experience extraction using line-level heuristics.
    Returns a list of simple job/experience records.
    """
    experience_records = []
    lines = clean_lines(section_text)

    for line in lines:
        lower_line = line.lower()

        if any(hint in lower_line for hint in JOB_HINTS):
            record = {
                "role_text": line,
                "year_mentions": re.findall(r'(?:19|20)\d{2}', line),
            }
            experience_records.append(record)

    return experience_records