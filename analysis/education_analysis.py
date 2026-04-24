from typing import List, Dict

def analyze_education_profile(profile: Dict) -> Dict:

    education_records = profile.get("education", [])

    if not education_records:
        return {
            "education_table": [],
            "education_summary": "No education data available."
        }

    table = []

    for record in education_records:
        table.append({
            "Degree": record.get("degree", "N/A"),
            "Institution": record.get("institution", "N/A"),
            "Year": record.get("year", "N/A"),
            "Score": record.get("grade", "N/A"),
        })

    summary = f"{len(table)} education record(s) found."

    return {
        "education_table": table,
        "education_summary": summary
    }