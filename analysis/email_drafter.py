"""
email_drafter.py

Missing information detection and personalized email drafting.
Supports both single-candidate and batch email generation.
"""


def classify_missing_info(parsed_profile):
    """
    Classify missing, incomplete, and unclear information in a CV.
    Returns categorized lists.
    """
    missing = []
    incomplete = []
    unclear = []

    pi = parsed_profile.get("personal_information", {})
    if not pi.get("email"):
        missing.append("Email address")
    if not pi.get("phone"):
        missing.append("Phone number")
    if not pi.get("dob"):
        missing.append("Date of birth")

    # Education checks
    for edu in parsed_profile.get("education", []):
        degree = edu.get("degree", "Unknown degree")
        if not edu.get("grade"):
            incomplete.append(f"Grade/CGPA missing for: {degree}")
        if not edu.get("year") and not edu.get("end_year"):
            incomplete.append(f"Passing year missing for: {degree}")
        if not edu.get("institution"):
            incomplete.append(f"Institution missing for: {degree}")
        if not edu.get("specialization"):
            incomplete.append(f"Specialization missing for: {degree}")

    # Experience checks
    for exp in parsed_profile.get("experience", []):
        title = exp.get("title", "Unknown role")
        if not exp.get("start_year") and not exp.get("start_date") and not exp.get("duration"):
            incomplete.append(f"Start date missing for: {title}")
        if not exp.get("end_year") and not exp.get("end_date") and not exp.get("duration"):
            incomplete.append(f"End date missing for: {title}")
        if not exp.get("organization"):
            incomplete.append(f"Organization missing for: {title}")

    # Publication checks
    for pub in parsed_profile.get("publications", []):
        if isinstance(pub, str):
            continue
        if len(pub.get("title", "")) < 15:
            continue
        title = pub.get("title", "Unknown")
        if not pub.get("year"):
            unclear.append(f"Publication year unclear: {title}")
        if not pub.get("venue"):
            incomplete.append(f"Venue missing for: {title}")
        if not pub.get("authors") and not pub.get("candidate_position"):
            unclear.append(f"Authorship role unclear: {title}")

    # Supervision checks
    if not parsed_profile.get("supervision"):
        unclear.append("Supervision record not provided - were any MS/PhD students supervised?")

    # Patent checks - only flag if the profile seems research-heavy
    total_pubs = len(parsed_profile.get("publications", []))
    if total_pubs > 5 and not parsed_profile.get("patents"):
        unclear.append("No patents listed - does the candidate hold any patents?")

    return {
        "missing":    list(set(missing)),
        "incomplete": list(set(incomplete)),
        "unclear":    list(set(unclear)),
        "total_issues": len(set(missing)) + len(set(incomplete)) + len(set(unclear)),
    }


def generate_email(candidate_name, missing_info, position=""):
    """Generate a personalized email requesting missing information."""
    missing = missing_info.get("missing", [])
    incomplete = missing_info.get("incomplete", [])
    unclear = missing_info.get("unclear", [])

    if not missing and not incomplete and not unclear:
        return {
            "subject": "",
            "body": "No missing information - email not required.",
            "required": False,
        }

    position_text = f" for the position of {position}" if position else ""
    subject = f"Application Follow-Up - Additional Information Required"

    sections = []
    if missing:
        sections.append(
            "The following information is absent from your CV:\n" +
            "\n".join(f"  * {i}" for i in missing)
        )
    if incomplete:
        sections.append(
            "The following fields are incomplete or partially provided:\n" +
            "\n".join(f"  * {i}" for i in incomplete)
        )
    if unclear:
        sections.append(
            "The following require clarification:\n" +
            "\n".join(f"  * {i}" for i in unclear)
        )

    body = (
        f"Dear {candidate_name or 'Candidate'},\n\n"
        f"Thank you for submitting your application{position_text}. "
        f"After a detailed review of your CV, we have identified some "
        f"information that is either missing, incomplete, or requires "
        f"clarification.\n\n"
        f"We kindly request you to address the following:\n\n"
        f"{chr(10).join(sections)}\n\n"
        f"Please reply with an updated CV or provide written clarification "
        f"at your earliest convenience. This will help us complete your "
        f"evaluation in a fair and thorough manner.\n\n"
        f"Best regards,\n"
        f"TALASH Recruitment System\n"
        f"HR Department, SEECS - NUST"
    )

    return {
        "subject": subject,
        "body": body,
        "required": True,
    }


def analyze_missing_and_draft_email(parsed_profile):
    """
    Main entry point - analyze missing info and draft email for a single candidate.
    """
    name = parsed_profile.get("personal_information", {}).get("name", "Candidate")
    position = parsed_profile.get("personal_information", {}).get("position_applied", "")
    missing_info = classify_missing_info(parsed_profile)
    email = generate_email(name, missing_info, position)

    return {
        "candidate_name":     name,
        "missing_info_analysis": missing_info,
        "email_draft":        email,
    }


def batch_draft_emails(profiles_list):
    """
    Generate personalized draft emails for multiple candidates.
    profiles_list: list of parsed profile dicts.
    Returns list of email results.
    """
    results = []
    for profile in profiles_list:
        result = analyze_missing_and_draft_email(profile)
        results.append(result)
    return results