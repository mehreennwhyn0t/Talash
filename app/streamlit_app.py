def process_single_cv(pdf_path: Path) -> dict:
    """Process a single CV and return full analysis."""
    text = extract_text_from_pdf(pdf_path)
    profile = parse_candidate_profile(text, use_llm=True)

    edu = analyze_education_profile(profile)
    exp = analyze_experience(profile)
    res = analyze_research_profile(profile)

    publications = []
    if isinstance(res.get("publications_table"), pd.DataFrame):
        publications = res["publications_table"].to_dict("records")
    elif isinstance(profile.get("publications"), list):
        publications = profile.get("publications", [])

    topic_result    = analyze_topic_variability(publications)
    candidate_name  = profile.get("personal_information", {}).get("name", "")
    coauthor_result = analyze_coauthors(publications, candidate_name)
    sbp_result      = analyze_supervision_books_patents(profile)
    skill_result    = analyze_skill_alignment(profile)
    email_result    = analyze_missing_and_draft_email(profile)
    summary         = generate_summary(edu, exp, res, email_result["missing_info_analysis"])

    return {
        "filename":                 pdf_path.name,
        "raw_text":                 text,
        "profile":                  profile,
        "education":                edu,
        "experience":               exp,
        "research":                 res,
        "topic_analysis":           topic_result,
        "coauthor_analysis":        coauthor_result,
        "supervision_books_patents": sbp_result,
        "skill_alignment":          skill_result,
        "email_result":             email_result,
        "summary":                  summary,
    }