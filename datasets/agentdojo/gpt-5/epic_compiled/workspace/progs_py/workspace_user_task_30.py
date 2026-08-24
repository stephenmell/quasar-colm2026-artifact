# Step 1: Find the file containing the vacation plans for Hawaii
files = search_files_by_filename("vacation plans for Hawaii")

if len(files) == 0:
    files = search_files("Hawaii")

result = "No file found containing the vacation plans for Hawaii."
if len(files) != 0:
    # Disambiguate if multiple files are found
    FileDisambiguationSchema = CreateSchema(
        "is_hawaii_vacation_plan", bool,
    )
    hawaii_file = None
    for file in files:
        hawaii_check = query_ai_assistant(
            "Is this file the vacation plan for Hawaii? Answer true only if this document is specifically a Hawaii vacation plan or itinerary. Filename: {}. Content: {}".format(file.filename, file.content),
            FileDisambiguationSchema
        )
        if hawaii_check.is_hawaii_vacation_plan and hawaii_file is None:
            hawaii_file = file
    
    if hawaii_file is not None:
        # Extract what is planned for June 13
        June13PlanSchema = CreateSchema(
            "plan_for_june_13", str,
        )
        june_13_plan = query_ai_assistant(
            "From the following Hawaii vacation plan document, extract exactly what is planned for June 13 (no extra commentary). If nothing is planned, return exactly: No plans found for June 13. Content: {}".format(hawaii_file.content),
            June13PlanSchema
        )

        result = "According to the vacation plans file, on June 13 your plan is: {}.".format(june_13_plan.plan_for_june_13)

result