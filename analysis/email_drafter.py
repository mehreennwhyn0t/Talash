def classify_missing_info(parsed_profile):
    missing = []
    incomplete = []
    unclear = []

    if not parsed_profile.get("personal_information", {}).get("email"):
        missing.append("Email")

    for edu in parsed_profile.get("education", []):
        if not edu.get("score"):
            incomplete.append("Education score missing")

    for exp in parsed_profile.get("experience", []):
        if not exp.get("start_date") or not exp.get("end_date"):
            incomplete.append(f"Incomplete dates in {exp.get('organization')}")

    for pub in parsed_profile.get("publications", []):
        if not pub.get("year"):
            unclear.append("Publication year unclear")

    return {
    "missing": list(set(missing)),
    "incomplete": list(set(incomplete)),
    "unclear": list(set(unclear))
    }

def generate_email(candidate_name, missing_info):
    subject = "Request for Additional Information"

    body = f"""
Dear {candidate_name},

Thank you for your application.

We noticed that some information in your CV is missing or incomplete:

Missing:
{', '.join(missing_info.get('missing', []))}

Incomplete:
{', '.join(missing_info.get('incomplete', []))}

Unclear:
{', '.join(missing_info.get('unclear', []))}

Kindly provide the missing details or an updated CV.

Best regards,
Recruitment Team
"""

    return {
        "subject": subject,
        "body": body.strip()
    }