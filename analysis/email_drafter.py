def classify_missing_info(parsed_profile):
    missing    = []
    incomplete = []
    unclear    = []

    pi = parsed_profile.get("personal_information", {})
    if not pi.get("email"):
        missing.append("Email address")
    if not pi.get("phone"):
        missing.append("Phone number")
    if not pi.get("dob"):
        missing.append("Date of birth")

    for edu in parsed_profile.get("education", []):
        degree = edu.get("degree", "Unknown degree")[:50]
        if not edu.get("grade"):
            incomplete.append(f"Grade/CGPA missing for: {degree}")
        if not edu.get("year"):
            incomplete.append(f"Passing year missing for: {degree}")
        if not edu.get("institution"):
            incomplete.append(f"Institution missing for: {degree}")

    for exp in parsed_profile.get("experience", []):
        title = exp.get("title", "Unknown role")[:50]
        if not exp.get("start_year") and not exp.get("duration"):
            incomplete.append(f"Start date missing for: {title}")
        if not exp.get("end_year") and not exp.get("duration"):
            incomplete.append(f"End date missing for: {title}")

    for pub in parsed_profile.get("publications", []):
        # Skip entries that look like parser artifacts
        if len(pub.get("title", "")) < 15:
            continue
        title = pub.get("title", "Unknown")[:60]
        if not pub.get("year"):
            unclear.append(f"Publication year unclear: {title}")
        if not pub.get("venue"):
            incomplete.append(f"Venue missing for: {title}")

    return {
        "missing":    list(set(missing)),
        "incomplete": list(set(incomplete)),
        "unclear":    list(set(unclear))
    }


def generate_email(candidate_name, missing_info):
    missing    = missing_info.get("missing", [])
    incomplete = missing_info.get("incomplete", [])
    unclear    = missing_info.get("unclear", [])

    if not missing and not incomplete and not unclear:
        return {"subject": "", "body": "No missing information — email not required."}

    subject = "Application Follow-Up — Additional Information Required"

    sections = []
    if missing:
        sections.append(
            "The following information is absent from your CV:\n" +
            "\n".join(f"  - {i}" for i in missing)
        )
    if incomplete:
        sections.append(
            "The following fields are incomplete:\n" +
            "\n".join(f"  - {i}" for i in incomplete)
        )
    if unclear:
        sections.append(
            "The following require clarification:\n" +
            "\n".join(f"  - {i}" for i in unclear)
        )

    body = (
        f"Dear {candidate_name or 'Candidate'},\n\n"
        f"Thank you for your application. After reviewing your CV, we require "
        f"some additional information before proceeding.\n\n"
        f"{chr(10).join(sections)}\n\n"
        f"Please reply with an updated CV or written clarification at your "
        f"earliest convenience.\n\n"
        f"Best regards,\n"
        f"TALASH Recruitment System\n"
        f"HR Department, SEECS — NUST"
    )

    return {"subject": subject, "body": body}


def analyze_missing_and_draft_email(parsed_profile):
    """Main entry point — Member 3 calls this."""
    name         = parsed_profile.get("personal_information", {}).get("name", "Candidate")
    missing_info = classify_missing_info(parsed_profile)
    email        = generate_email(name, missing_info)
    return {
        "missing_info_analysis": missing_info,
        "email_draft":           email
    }