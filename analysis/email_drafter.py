"""
email_drafter.py

Missing information detection and personalized email drafting.
Milestone 3 version.

Supports:
- Basic personal information missing checks
- Education missing/incomplete checks
- Experience missing/incomplete checks
- Publication verification/authorship checks
- Supervision/books/patents clarification
- Skill evidence clarification
- Single and batch email generation
"""


def _is_empty(value):
    if value is None:
        return True

    if isinstance(value, str):
        return value.strip() == "" or value.strip().lower() in {
            "n/a",
            "na",
            "none",
            "not available",
            "-",
            "null",
            "unknown",
        }

    if isinstance(value, list):
        return len(value) == 0

    if isinstance(value, dict):
        return len(value) == 0

    return False


def _personal_info(parsed_profile):
    return parsed_profile.get("personal_information", {}) or {}


def _candidate_name(parsed_profile):
    pi = _personal_info(parsed_profile)
    return pi.get("name") or parsed_profile.get("name") or "Candidate"


def classify_missing_info(parsed_profile, skill_alignment=None):
    """
    Classify missing, incomplete, and unclear information in a CV.
    This preserves the existing M2 function name and extends it for M3.
    """
    missing = []
    incomplete = []
    unclear = []

    pi = _personal_info(parsed_profile)

    if not pi.get("name"):
        missing.append("Candidate name")

    if not pi.get("email"):
        missing.append("Email address")

    if not pi.get("phone"):
        missing.append("Phone number")

    if not pi.get("dob"):
        missing.append("Date of birth")

    if not pi.get("position_applied"):
        missing.append("Position applied for")

    education = parsed_profile.get("education", [])

    if not education:
        missing.append("Education records")

    for edu in education:
        if not isinstance(edu, dict):
            continue

        degree = edu.get("degree") or edu.get("title") or "Unknown degree"

        if not edu.get("grade") and not edu.get("cgpa") and not edu.get("marks") and not edu.get("percentage"):
            incomplete.append(f"Grade/CGPA/marks missing for: {degree}")

        if not edu.get("year") and not edu.get("end_year") and not edu.get("completion_year") and not edu.get("passing_year"):
            incomplete.append(f"Passing/completion year missing for: {degree}")

        if not edu.get("institution") and not edu.get("university"):
            incomplete.append(f"Institution missing for: {degree}")

        if not edu.get("specialization") and not edu.get("discipline"):
            incomplete.append(f"Specialization/discipline missing for: {degree}")

    experience = parsed_profile.get("experience", [])

    if not experience:
        missing.append("Professional experience records")

    for exp in experience:
        if not isinstance(exp, dict):
            continue

        title = exp.get("title") or exp.get("job_title") or exp.get("position") or "Unknown role"

        if not exp.get("title") and not exp.get("job_title") and not exp.get("position"):
            incomplete.append(f"Job title missing for: {title}")

        if not exp.get("start_year") and not exp.get("start_date") and not exp.get("duration"):
            incomplete.append(f"Start date missing for: {title}")

        if not exp.get("end_year") and not exp.get("end_date") and not exp.get("duration"):
            incomplete.append(f"End date missing for: {title}")

        if not exp.get("organization") and not exp.get("org") and not exp.get("company") and not exp.get("institution"):
            incomplete.append(f"Organization missing for: {title}")

        if str(exp.get("duration", "")).strip().lower() in {"present", "current"}:
            unclear.append(f"Duration unclear for: {title}. Start date is required.")

    publications = parsed_profile.get("publications", [])

    if not publications:
        missing.append("Publication records")

    for pub in publications:
        if isinstance(pub, str):
            continue

        if not isinstance(pub, dict):
            continue

        title = pub.get("title") or "Unknown publication"

        if not pub.get("title"):
            incomplete.append("Publication title missing")

        if not pub.get("year"):
            unclear.append(f"Publication year unclear: {title}")

        if not pub.get("venue") and not pub.get("journal") and not pub.get("conference"):
            incomplete.append(f"Venue missing for: {title}")

        if not pub.get("authors"):
            incomplete.append(f"Author list missing for: {title}")

        if not pub.get("authorship_role") and not pub.get("candidate_position"):
            unclear.append(f"Authorship role unclear: {title}")

        publication_type = str(pub.get("type", "")).lower()

        if not publication_type:
            unclear.append(f"Publication type unclear: {title}")

        if publication_type == "journal":
            if not pub.get("issn"):
                incomplete.append(f"ISSN missing for journal paper: {title}")

            if not pub.get("quartile"):
                unclear.append(f"Journal quartile/ranking unverified for: {title}")

            if not pub.get("wos_indexed") and not pub.get("scopus_indexed"):
                unclear.append(f"WoS/Scopus indexing status unverified for: {title}")

        if publication_type == "conference":
            if not pub.get("conference_rank"):
                unclear.append(f"Conference ranking unverified for: {title}")

            if not pub.get("proceedings_publisher") and not pub.get("publisher"):
                incomplete.append(f"Proceedings publisher missing for conference paper: {title}")

    supervision = parsed_profile.get("supervision", [])

    if not supervision:
        unclear.append("Supervision record not provided - please confirm whether any MS/PhD students were supervised or co-supervised.")

    for sup in supervision:
        if not isinstance(sup, dict):
            continue

        student = sup.get("student_name") or "Unknown supervised student"

        if not sup.get("student_name"):
            incomplete.append("Supervised student name missing")

        if not sup.get("degree_level"):
            incomplete.append(f"MS/PhD level missing for supervision record: {student}")

        if not sup.get("role"):
            incomplete.append(f"Main/co-supervisor role missing for: {student}")

        if not sup.get("graduation_year"):
            incomplete.append(f"Graduation year missing for supervised student: {student}")

    books = parsed_profile.get("books", [])

    if not books:
        unclear.append("Book authorship record not provided - please confirm whether any books were authored or co-authored.")

    for book in books:
        if not isinstance(book, dict):
            continue

        title = book.get("title") or book.get("book_name") or "Unknown book"

        if not book.get("title") and not book.get("book_name"):
            incomplete.append("Book title missing")

        if not book.get("authors"):
            incomplete.append(f"Authors missing for book: {title}")

        if not book.get("isbn"):
            incomplete.append(f"ISBN missing for book: {title}")

        if not book.get("publisher"):
            incomplete.append(f"Publisher missing for book: {title}")

        if not book.get("year") and not book.get("publishing_year"):
            incomplete.append(f"Publishing year missing for book: {title}")

        if not book.get("link") and not book.get("online_link"):
            incomplete.append(f"Online verification link missing for book: {title}")

    patents = parsed_profile.get("patents", [])

    if not patents:
        unclear.append("Patent record not provided - please confirm whether any patents or intellectual property records exist.")

    for patent in patents:
        if not isinstance(patent, dict):
            continue

        title = patent.get("title") or patent.get("patent_title") or "Unknown patent"

        if not patent.get("patent_number"):
            incomplete.append(f"Patent number missing for: {title}")

        if not patent.get("title") and not patent.get("patent_title"):
            incomplete.append("Patent title missing")

        if not patent.get("inventors") and not patent.get("innovators"):
            incomplete.append(f"Inventors/innovators missing for patent: {title}")

        if not patent.get("date"):
            incomplete.append(f"Patent date missing for: {title}")

        if not patent.get("country") and not patent.get("country_of_filing"):
            incomplete.append(f"Country of filing missing for patent: {title}")

        if not patent.get("link") and not patent.get("verification_link"):
            incomplete.append(f"Verification link missing for patent: {title}")

    if skill_alignment:
        for skill in skill_alignment.get("weakly_evidenced", []):
            unclear.append(f"Skill evidence unclear: {skill}")

        for skill in skill_alignment.get("unsupported", []):
            unclear.append(f"Claimed skill appears unsupported by extracted profile: {skill}")

    missing = sorted(set(missing))
    incomplete = sorted(set(incomplete))
    unclear = sorted(set(unclear))

    return {
        "missing": missing,
        "incomplete": incomplete,
        "unclear": unclear,
        "total_issues": len(missing) + len(incomplete) + len(unclear),
    }


def detect_missing_information(parsed_profile, skill_alignment=None):
    """
    New M3-friendly alias.
    """
    return classify_missing_info(parsed_profile, skill_alignment=skill_alignment)


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
    subject = "Application Follow-Up - Additional Information Required"

    sections = []

    if missing:
        sections.append(
            "The following information is absent from your CV:\n"
            + "\n".join(f"  * {item}" for item in missing)
        )

    if incomplete:
        sections.append(
            "The following fields are incomplete or partially provided:\n"
            + "\n".join(f"  * {item}" for item in incomplete)
        )

    if unclear:
        sections.append(
            "The following require clarification:\n"
            + "\n".join(f"  * {item}" for item in unclear)
        )

    body = (
        f"Dear {candidate_name or 'Candidate'},\n\n"
        f"Thank you for submitting your application{position_text}. "
        f"After a detailed review of your CV, we identified some information "
        f"that is missing, incomplete, or requires clarification.\n\n"
        f"We kindly request you to address the following:\n\n"
        f"{chr(10).join(sections)}\n\n"
        f"Please reply with an updated CV or provide written clarification "
        f"at your earliest convenience. This will help us complete your "
        f"evaluation in a fair and evidence-based manner.\n\n"
        f"Best regards,\n"
        f"TALASH Recruitment System\n"
        f"HR Department, SEECS - NUST"
    )

    return {
        "subject": subject,
        "body": body,
        "required": True,
    }


def draft_missing_information_email(parsed_profile, issues=None, skill_alignment=None):
    """
    New M3-friendly email drafting function.
    """
    name = _candidate_name(parsed_profile)
    position = _personal_info(parsed_profile).get("position_applied", "")

    if issues is None:
        issues = classify_missing_info(parsed_profile, skill_alignment=skill_alignment)

    email = generate_email(name, issues, position)

    return {
        "required": email["required"],
        "subject": email["subject"],
        "body": email["body"],
        "issues": issues,
    }


def analyze_missing_and_draft_email(parsed_profile, skill_alignment=None):
    """
    Main entry point - analyze missing info and draft email for a single candidate.
    Preserves the existing function name.
    """
    name = _candidate_name(parsed_profile)
    position = _personal_info(parsed_profile).get("position_applied", "")

    missing_info = classify_missing_info(parsed_profile, skill_alignment=skill_alignment)
    email = generate_email(name, missing_info, position)

    return {
        "candidate_name": name,
        "missing_info_analysis": missing_info,
        "email_draft": email,
    }


def batch_draft_emails(profiles_list, skill_alignment_results=None):
    """
    Generate personalized draft emails for multiple candidates.
    Preserves existing function name.
    """
    results = []

    for profile in profiles_list:
        name = _candidate_name(profile)
        skill_alignment = None

        if isinstance(skill_alignment_results, dict):
            skill_alignment = skill_alignment_results.get(name)

        result = analyze_missing_and_draft_email(profile, skill_alignment=skill_alignment)
        results.append(result)

    return results


def batch_draft_missing_information_emails(profiles_list, skill_alignment_results=None):
    """
    New M3-friendly batch alias.
    """
    return batch_draft_emails(profiles_list, skill_alignment_results=skill_alignment_results)