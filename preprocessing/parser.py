"""
parser.py — CV parser tuned for the NUST HR portal CV format.

Each CV follows this structure:
  Page 1: Header (name, personal info) → Education table
  Page 2: Professional Qualifications → Civil Experience table → Publications table
  Page 3+: More publications → References

All tables are space-aligned (not real HTML tables), extracted as plain text lines.
"""

import re

# ── Regex patterns ────────────────────────────────────────────────────────────
EMAIL_RE    = re.compile(r'[\w\.\-\+]+@[\w\.\-]+\.\w{2,}')
PHONE_RE    = re.compile(r'(\+92[\s\-]?\d{3}[\s\-]?\d{7}|\+\d{1,3}[\s\-]?\d{6,12}|0\d{3}[\s\-]?\d{7})')
YEAR_RE     = re.compile(r"\b((?:19|20)\d{2})\b")
DURATION_RE = re.compile(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[\-\s]\d{4}\s*[-–]\s*(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[\-\s]\d{4}|(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[\-\s]\d{4}\s*[-–]\s*Present', re.I)

DEGREE_KEYWORDS = ["phd", "ph.d", "doctorate", "ms ", "msc", "m.sc", "mphil", "m.phil",
                   "masters", "master of", "be ", "b.e", "bsc", "b.sc", "bs ", "b.s",
                   "bachelor", "hssc", "fsc", "f.sc", "pre-engineering", "pre engineering",
                   "ssc", "matric", "intermediate", "a-levels", "o-levels"]

JOB_KEYWORDS = ["professor", "lecturer", "engineer", "manager", "director", "coordinator",
                "researcher", "analyst", "developer", "consultant", "officer", "assistant",
                "associate", "head", "dean", "principal", "supervisor", "instructor",
                "scientist", "specialist", "advisor", "architect", "lead"]


# ── Section splitter ──────────────────────────────────────────────────────────
def split_into_sections(lines):
    """
    Splits raw CV lines into named sections based on header keywords.
    Returns dict: section_name -> list of lines
    """
    SECTION_MARKERS = {
        "education":     ["education"],
        "experience":    ["civil experience", "professional experience", "work experience", "employment history"],
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


# ── Personal information ──────────────────────────────────────────────────────
def extract_personal_information(header_lines, full_text):
    info = {"name": "", "email": "", "phone": "", "position_applied": "", "dob": ""}

    full = "\n".join(header_lines)

    # Position applied
    pos_m = re.search(r'Candidate for the Post of (.+?)(?:\(Apply Date|$)', full, re.I)
    if pos_m:
        info["position_applied"] = pos_m.group(1).strip()

    # Name — appears as "Name FIRSTNAME LASTNAME  Father's..."
    name_m = re.search(r'\bName\s+([A-Za-z][A-Za-z\s\.]{2,60?}?)\s+(?:Father|Guardian|Date/Place)', full, re.I)
    if name_m:
        info["name"] = name_m.group(1).strip().title()
    else:
        # Fallback: second non-empty line after "Candidate for the Post"
        for i, line in enumerate(header_lines):
            if "Candidate for the Post" in line:
                for j in range(i+1, min(i+5, len(header_lines))):
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

    # Email and phone — only search before "References" section
    # to avoid picking up referee contact details
    ref_idx = full_text.lower().find("references")
    search_text = full_text[:ref_idx] if ref_idx > 200 else full_text

    email_m = EMAIL_RE.search(search_text)
    if email_m:
        info["email"] = email_m.group(0)

    phone_m = PHONE_RE.search(search_text)
    if phone_m:
        info["phone"] = phone_m.group(0).strip()

    return info


# ── Education ─────────────────────────────────────────────────────────────────
def extract_education(edu_lines):
    """
    Education table columns (space-aligned):
      Name of Degree | Specialization | Grade/%age/GPA | Passing Year | Board/University
    """
    entries = []
    # Skip header row
    data_lines = [l for l in edu_lines if l.strip()
                  and not re.match(r'^Name of Degree', l, re.I)
                  and not re.match(r'^(Grade|Specialization|Passing|Board)', l, re.I)]

    for line in data_lines:
        stripped = line.strip()
        if not stripped:
            continue
        lower = stripped.lower()
        if not any(kw in lower for kw in DEGREE_KEYWORDS):
            continue

        # Extract passing year
        years = YEAR_RE.findall(stripped)
        year = years[-1] if years else ""

        # Extract grade (number like 3.83, 69.84, 88%, 76%)
        grade_m = re.search(r'\b(\d{1,3}\.?\d{0,2})\s*(%|\/\s*\d+\.?\d*)?\b', stripped)
        grade = ""
        if grade_m:
            grade = grade_m.group(0).strip()

        # University is usually after the year at the end of the line
        # Remove year and grade to isolate degree + university
        after_year = ""
        if year:
            year_idx = stripped.rfind(year)
            after_year = stripped[year_idx + len(year):].strip()

        # Degree: everything before the grade value
        degree_raw = stripped
        if grade:
            grade_idx = stripped.find(grade)
            degree_raw = stripped[:grade_idx].strip() if grade_idx > 5 else stripped

        # Clean degree name (remove trailing specialization noise)
        degree = re.sub(r'\s{2,}.*', '', degree_raw).strip()
        degree = degree[:80]

        entries.append({
            "degree": degree,
            "grade": grade,
            "year": year,
            "institution": after_year[:100] if after_year else ""
        })

    return entries


# ── Experience ────────────────────────────────────────────────────────────────
def extract_experience(exp_lines):
    """
    Civil Experience table columns:
      Name of Post | Organization | Location | Duration of Employment
    """
    entries = []
    data_lines = [l for l in exp_lines if l.strip()
                  and not re.match(r'^Name of Post', l, re.I)
                  and not re.match(r'^(Organization|Location|Duration)', l, re.I)]

    for line in data_lines:
        stripped = line.strip()
        if not stripped:
            continue
        lower = stripped.lower()
        if not any(kw in lower for kw in JOB_KEYWORDS):
            continue

        # Duration at the end: "Sep-2017 - Aug-2023" or "Jan-2025 - Present"
        dur_m = DURATION_RE.search(stripped)
        duration = dur_m.group(0).strip() if dur_m else ""

        # Years from duration
        years = YEAR_RE.findall(duration) if duration else YEAR_RE.findall(stripped)
        start_year = years[0] if len(years) > 0 else ""
        end_year   = years[1] if len(years) > 1 else ("Present" if "present" in stripped.lower() else "")

        # Title: usually the first word(s) before the org name
        title_part = stripped
        if dur_m:
            title_part = stripped[:dur_m.start()].strip()

        # Split title from org by finding where job keywords end
        title = ""
        organization = ""
        for kw in JOB_KEYWORDS:
            kw_m = re.search(r'\b' + kw + r'\b', title_part, re.I)
            if kw_m:
                end_of_title = kw_m.end()
                # find next capitalized word cluster as title end
                title = title_part[:end_of_title].strip()
                organization = title_part[end_of_title:].strip().lstrip(',').strip()
                break
        if not title:
            title = title_part[:50]

        entries.append({
            "title": title[:80],
            "organization": organization[:100],
            "start_year": start_year,
            "end_year": end_year,
            "duration": duration
        })

    return entries


# ── Publications ──────────────────────────────────────────────────────────────
def extract_publications(pub_lines):
    """
    Publications table columns:
      Paper Title | Name of Author | CO-Author | Published In | No | Impact Factor | Vol | PP | Date
    The title spans multiple lines until the author's name appears.
    """
    entries = []
    # Skip header
    data_lines = [l for l in pub_lines if l.strip()
                  and not re.match(r'^Paper Title', l, re.I)
                  and not re.match(r'^(Name of Author|Name of CO|Published|Impact|Factor|No\b)', l, re.I)]

    current_title_parts = []
    current_venue = ""
    current_type = ""
    current_year = ""
    current_impact = ""

    def flush(parts, venue, pub_type, year, impact):
        if parts:
            title = " ".join(parts).strip()
            # Clean up author name fragments that got mixed in
            title = re.sub(r'\s+', ' ', title)
            entries.append({
                "title": title[:200],
                "venue": venue,
                "type": pub_type,
                "year": year,
                "impact_factor": impact
            })

    for line in data_lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Detect a publication venue keyword → this line has venue info
        if re.search(r'\b(Journal|Conference|Workshop|Symposium|Proceedings)\b', stripped, re.I):
            # Extract venue type
            venue_m = re.search(r'(International Journal|Journal|International Conference|Conference|Workshop|Symposium)', stripped, re.I)
            current_venue = venue_m.group(0) if venue_m else ""
            current_type = "Journal" if "journal" in current_venue.lower() else "Conference"
            # Extract impact factor
            impact_m = re.search(r'\b(\d+\.\d{2})\b', stripped)
            current_impact = impact_m.group(0) if impact_m else ""
            # Extract year
            years = YEAR_RE.findall(stripped)
            current_year = years[-1] if years else ""
            # Flush current entry
            flush(current_title_parts, current_venue, current_type, current_year, current_impact)
            current_title_parts = []
            current_venue = ""
            current_type = ""
            current_year = ""
            current_impact = ""
        else:
            # Accumulate title lines — skip lines that look like author names only
            # (short, all proper nouns, no sentence structure)
            if len(stripped.split()) >= 3:
                current_title_parts.append(stripped)

    flush(current_title_parts, current_venue, current_type, current_year, current_impact)

    return entries[:15]


# ── Skills ────────────────────────────────────────────────────────────────────
def extract_skills(skills_lines, full_text):
    """
    Try dedicated skills section first; fall back to keyword scan of full text.
    """
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

    # Check dedicated section first
    section_text = " ".join(skills_lines)
    if len(section_text.strip()) > 20:
        for skill in SKILL_KEYWORDS:
            if re.search(r'\b' + re.escape(skill) + r'\b', section_text, re.I):
                found.append(skill)

    # Always also scan full text for technical skills (they often appear in pub titles/experience)
    for skill in SKILL_KEYWORDS:
        if skill not in found and re.search(r'\b' + re.escape(skill) + r'\b', full_text, re.I):
            found.append(skill)

    return sorted(set(found))


# ── Missing information flags ─────────────────────────────────────────────────
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
        missing.append("Education records not detected — check CV format")
    if not profile.get("experience"):
        missing.append("Work experience not detected — check CV format")
    if not profile.get("publications"):
        missing.append("No publications detected")

    # Check for missing grades
    for edu in profile.get("education", []):
        if not edu.get("grade"):
            missing.append(f"Grade/CGPA missing for: {edu.get('degree', 'unknown degree')[:50]}")
            break

    return missing


# ── Main entry point ──────────────────────────────────────────────────────────
def parse_candidate_profile(text):
    """
    Main parser. Accepts raw extracted text from a CV PDF.
    Returns a structured profile dict.
    """
    lines = text.splitlines()
    sections = split_into_sections(lines)

    full_text = text  # keep for regex searches

    profile = {
        "personal_information": extract_personal_information(
            sections.get("header", []), full_text
        ),
        "education":    extract_education(sections.get("education", [])),
        "experience":   extract_experience(sections.get("experience", [])),
        "publications": extract_publications(sections.get("publications", [])),
        "skills":       extract_skills(sections.get("skills", []), full_text),
    }

    profile["missing_information"] = detect_missing(profile)

    return profile
