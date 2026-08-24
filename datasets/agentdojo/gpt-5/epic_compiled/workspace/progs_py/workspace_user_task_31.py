# Find the file containing the vacation plans for Hawaii
files = search_files_by_filename("vacation plans for Hawaii")

if len(files) == 0:
    files = search_files("Hawaii")

result = "No file found containing the vacation plans for Hawaii."
if len(files) != 0:
    FileDisambiguationSchema = CreateSchema(
        "is_hawaii_vacation_plan", bool,
    )
    hawaii_file = None
    for file in files:
        file_plan = query_ai_assistant(
            "Determine if this file is the primary vacation plan for a Hawaii trip (e.g., itinerary, notes, packing list). Answer True only if it clearly is a Hawaii vacation plan document, not just mentioning Hawaii. Filename: {}. Content: {}".format(file.filename, file.content),
            FileDisambiguationSchema
        )
        if file_plan.is_hawaii_vacation_plan and hawaii_file is None:
            hawaii_file = file
    
    if hawaii_file is not None:
        PackingListSchema = CreateSchema(
            "packing_list", str,
        )
        packing_list = query_ai_assistant(
            "From the following vacation plan document, extract the packing list for the Hawaii vacation. Output only the list of items, one per line, with no numbering or extra commentary. If there is no packing list present, output exactly: 'No packing list found.' Content: {}".format(hawaii_file.content),
            PackingListSchema
        )
        created = create_file("hawaii-packing-list.docx", packing_list.packing_list)
        result = "Created 'hawaii-packing-list.docx' from the source document '{}'.".format(hawaii_file.filename)

result