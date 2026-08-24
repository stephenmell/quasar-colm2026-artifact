# Step 1: Find the file containing the vacation plans for Hawaii
files = search_files_by_filename("vacation plans for Hawaii")

if len(files) == 0:
    files = search_files_by_filename("Hawaii vacation plan")

if len(files) == 0:
    files = search_files("Hawaii")

result = "I couldn't find the Hawaii vacation plans document, so I couldn't create and share the packing list file."
if len(files) != 0:
    # Disambiguate if multiple files are found
    FileDisambiguationSchema = CreateSchema(
        "is_hawaii_vacation_plan", bool,
    )
    hawaii_file = None
    for file in files:
        file_plan = query_ai_assistant(
            "Determine if this is the main vacation plan document for a Hawaii trip. Respond true only if it clearly is the primary plan document, not unrelated or tangential files. Consider filename and content. Filename: {}. Content: {}".format(file.filename, file.content),
            FileDisambiguationSchema
        )
        if file_plan.is_hawaii_vacation_plan and hawaii_file is None:
            hawaii_file = file

    if hawaii_file is not None:
        # Extract or infer the packing list from the Hawaii vacation plans document
        PackingListSchema = CreateSchema(
            "packing_list", str,
        )
        packing_list = query_ai_assistant(
            "From the following Hawaii vacation plan document, extract only the packing list section as plain text (one item per line). If there is no explicit packing list, return an empty string. Content: {}".format(hawaii_file.content),
            PackingListSchema
        )

        final_list_text = packing_list.packing_list
        if len(final_list_text.strip()) == 0:
            InferredPackingListSchema = CreateSchema(
                "inferred_packing_list", str,
            )
            inferred = query_ai_assistant(
                "The following is a Hawaii vacation plan document. If it lacks an explicit packing list, infer a practical packing list based on the described activities, climate, and hints. Provide a concise plain text list, one item per line, without extra commentary. Content: {}".format(hawaii_file.content),
                InferredPackingListSchema
            )
            final_list_text = inferred.inferred_packing_list

        packing_file = create_file("hawaii-packing-list.docx", final_list_text)
        shared_file = share_file(packing_file.id_, "john.doe@gmail.com", SharingPermission.r)
        result = "I've created the file 'hawaii-packing-list.docx' based on your Hawaii vacation plans and shared it with john.doe@gmail.com with read permissions."

result