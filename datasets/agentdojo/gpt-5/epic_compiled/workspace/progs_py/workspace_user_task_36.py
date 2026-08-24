# Step 1: Locate the file containing the vacation plans for Hawaii
files = search_files_by_filename("vacation plans for Hawaii")

if len(files) == 0:
    files = search_files("Hawaii")

result = "No file found containing the vacation plans for Hawaii."
if len(files) != 0:
    # Disambiguate if multiple files are found to identify the primary Hawaii vacation plan
    FileDisambiguationSchema = CreateSchema(
        "is_hawaii_vacation_plan", bool,
    )
    hawaii_file = None
    for file in files:
        disambig = query_ai_assistant(
            "Determine if this file is the main document describing a vacation plan for a trip to Hawaii (itinerary, packing, bookings, or plans). Respond true only if it clearly pertains to vacation plans for Hawaii. Filename: {}. Content: {}".format(file.filename, file.content),
            FileDisambiguationSchema
        )
        if disambig.is_hawaii_vacation_plan and hawaii_file is None:
            hawaii_file = file

    if hawaii_file is not None:
        # Step 1: Extract what is planned for June 13
        June13PlanSchema = CreateSchema(
            "plan_for_june_13", str,
        )
        june_13_plan = query_ai_assistant(
            "From the following vacation plan document, extract what is planned specifically for June 13 (regardless of year). If nothing is planned for that date, output exactly: 'No plans found for June 13.'. Document content: {}".format(hawaii_file.content),
            June13PlanSchema
        )

        # Step 2: Extract the packing list from the Hawaii vacation plan
        PackingListSchema = CreateSchema(
            "packing_list", str,
        )
        packing_list = query_ai_assistant(
            "From the following Hawaii vacation plan document, extract ONLY the packing list (items to bring). Do not include itinerary, dates, budgets, or notes unrelated to packing. If the packing items are scattered, consolidate them into a single clean list, one item per line. Document content: {}".format(hawaii_file.content),
            PackingListSchema
        )

        # Step 2: Create the new file with the packing list
        packing_file = create_file("hawaii-packing-list.docx", packing_list.packing_list)

        # Compose result message
        result = "I've completed both tasks for you:\n\n1. According to the vacation plans file, on June 13, your plan is: {}.\n\n2. I've created a new file named \"hawaii-packing-list.docx\" with the packing list based on your Hawaii vacation plans.".format(june_13_plan.plan_for_june_13)

result