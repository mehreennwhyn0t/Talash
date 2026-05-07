"""
prompts.py

All LLM prompts used by the TALASH system.
Each function returns a formatted prompt string ready to send to Gemini.
"""


def cv_parsing_prompt(raw_text: str) -> str:
    """Prompt to extract structured data from raw CV text."""
    return f"""You are an expert CV parser for a university recruitment system.
Extract structured information from the following CV text.

Return a JSON object with these exact keys:
{{
  "personal_information": {{
    "name": "",
    "email": "",
    "phone": "",
    "dob": "",
    "position_applied": ""
  }},
  "education": [
    {{
      "degree": "exact degree title",
      "specialization": "field/discipline",
      "institution": "university or board name",
      "grade": "CGPA or percentage as written",
      "grade_type": "cgpa_4 | cgpa_5 | percentage | division | grade",
      "start_year": "year or empty",
      "end_year": "year or empty"
    }}
  ],
  "experience": [
    {{
      "title": "job title",
      "organization": "employer name",
      "location": "city/country",
      "start_date": "Mon-YYYY or YYYY",
      "end_date": "Mon-YYYY or YYYY or Present",
      "employment_type": "full-time | part-time | contract | research",
      "responsibilities": "brief description if available"
    }}
  ],
  "publications": [
    {{
      "title": "paper title",
      "authors": ["author1", "author2"],
      "venue": "journal or conference name",
      "type": "journal | conference",
      "year": "YYYY",
      "impact_factor": "number or empty",
      "candidate_position": "first | corresponding | co-author | unknown"
    }}
  ],
  "skills": ["skill1", "skill2"],
  "supervision": [
    {{
      "student_name": "",
      "degree_level": "MS | PhD",
      "role": "main_supervisor | co_supervisor",
      "year": "",
      "thesis_title": ""
    }}
  ],
  "books": [
    {{
      "title": "",
      "authors": [],
      "publisher": "",
      "year": "",
      "isbn": ""
    }}
  ],
  "patents": [
    {{
      "title": "",
      "patent_number": "",
      "year": "",
      "inventors": []
    }}
  ],
  "certifications": ["cert1", "cert2"],
  "awards": ["award1"]
}}

IMPORTANT RULES:
* Extract ALL education records from school (SSC/Matric/O-Levels) through PhD
* Keep original grade/CGPA values exactly as written
* For publications, try to separate the actual paper title from author names
* Candidates may have "Father's Name" or "Guardian" listed; ensure you extract the Candidate's name, NOT the father's name.
* If a field is not found, use empty string "" or empty list []
* Do NOT invent or hallucinate information
* Return ONLY valid JSON, no markdown

CV TEXT:
{raw_text}"""


def education_analysis_prompt(education_records: list, experience_records: list) -> str:
    """Prompt to analyze educational profile."""
    import json
    return f"""You are an educational profile analyst for university recruitment.

Analyze the candidate's educational records and provide a detailed assessment.

Education Records:
{json.dumps(education_records, indent=2)}

Professional Experience (for gap justification):
{json.dumps(experience_records, indent=2)}

Return a JSON object with:
{{
  "education_levels": [
    {{
      "level": "SSC | HSSC | UG | PG | PhD",
      "degree": "degree title",
      "specialization": "field",
      "institution": "name",
      "original_score": "as written",
      "normalized_score": number_out_of_100_or_null,
      "year": "YYYY",
      "score_interpretation": "excellent | good | average | below_average"
    }}
  ],
  "degree_sequence": "e.g. SSC to HSSC to BE to MS to PhD",
  "academic_pathway": "standard_4year | traditional_2year | mixed",
  "progression_trend": "improving | declining | stable | inconsistent",
  "highest_qualification": "PhD | MS | BS etc",
  "specialization_consistency": "consistent | partially_consistent | inconsistent",
  "specialization_summary": "brief description of how specializations connect",
  "educational_gaps": [
    {{
      "between": "degree1 to degree2",
      "gap_years": number,
      "justified": true_or_false,
      "justification": "reason if justified by work experience"
    }}
  ],
  "total_gap_years": number,
  "academic_strength": "strong | moderate | weak",
  "interpretation": "2-3 sentence overall educational assessment"
}}

RULES:
* Normalize CGPA/4 to /100 by (cgpa/4)*100, CGPA/5 by (cgpa/5)*100
* Percentages stay as-is
* Identify gaps > 1 year between consecutive degrees
* Check if gaps are justified by employment during that period
* Assess if specialization is consistent across degrees
* Return ONLY valid JSON"""


def candidate_summary_prompt(
    name: str,
    education_analysis: dict,
    experience_analysis: dict,
    research_analysis: dict,
    missing_info: dict
) -> str:
    """Prompt to generate a comprehensive candidate summary."""
    import json
    return f"""You are a senior recruitment analyst. Generate a comprehensive candidate assessment.

Candidate: {name}

Education Analysis:
{json.dumps(education_analysis, indent=2)}

Experience Analysis:
{json.dumps(experience_analysis, indent=2)}

Research Analysis:
{json.dumps(research_analysis, indent=2)}

Missing Information:
{json.dumps(missing_info, indent=2)}

Return a JSON object:
{{
  "strengths": ["strength1", "strength2", ...],
  "concerns": ["concern1", "concern2", ...],
  "suitability_label": "Strong Candidate | Moderate Candidate | Needs Review",
  "overall_assessment": "3-5 sentence comprehensive assessment",
  "key_highlights": ["highlight1", "highlight2"],
  "recommendations": ["recommendation1", "recommendation2"]
}}

Be specific, evidence-based, and balanced. Return ONLY valid JSON."""


def research_analysis_prompt(publications: list, candidate_name: str) -> str:
    """Prompt to analyze research publications."""
    import json
    return f"""You are a research profile analyst. Analyze these publications for candidate: {candidate_name}

Publications:
{json.dumps(publications, indent=2)}

Return a JSON object:
{{
  "total_publications": number,
  "journal_papers": number,
  "conference_papers": number,
  "first_author_count": number,
  "corresponding_author_count": number,
  "co_author_count": number,
  "publications_by_year": {{"YYYY": count}},
  "research_themes": ["theme1", "theme2"],
  "dominant_theme": "main research area",
  "venue_quality_summary": "brief assessment of publication venues",
  "authorship_summary": "brief assessment of authorship roles",
  "research_summary": "2-3 sentence overall research assessment"
}}

Return ONLY valid JSON."""
