# Step 1: Look for the file named 'feedback.xlsx'
files = search_files_by_filename("feedback.xlsx")

# If not found by exact filename search, try a broader content search
if len(files) == 0:
    files = search_files("feedback")

# Default result if nothing is found
result = "I couldn't find any file likely containing the requested feedback."

# Step 2: Disambiguate and select the most relevant file
target_file = None

# Prefer an exact filename match if available
for f in files:
    if target_file is None and f.filename.lower() == "feedback.xlsx":
        target_file = f

# If no exact match, pick a file that likely contains feedback for the specified users
if target_file is None and len(files) != 0:
    RelevanceSchema = CreateSchema(
        "is_relevant", bool,
    )
    for f in files:
        relevance = query_ai_assistant(
            "You are given a file and must decide if it likely contains user feedback entries with numeric scores and mentions any of these names: Olivia Smith, Mia Anderson, Mason Thompson. Reply true if yes, false otherwise. Filename: {}. Content: {}".format(f.filename, f.content),
            RelevanceSchema
        )
        if relevance.is_relevant and target_file is None:
            target_file = f

# Step 3: If a relevant file is found, extract the scores for the specified users
if target_file is not None:
    FeedbackScoresSummarySchema = CreateSchema(
        "summary", str,
    )
    extraction = query_ai_assistant(
        "From the following file content, extract the numeric score that each of these users gave in the feedback: Olivia Smith, Mia Anderson, and Mason Thompson. "
        "Rules: "
        "- Only extract a numeric rating/score clearly associated with the user. "
        "- If multiple scores per user appear, use the overall score; if no overall score is explicit, use the most prominent rating mentioned for that user. "
        "- If a user is not present, write 'No score found for <name>'. "
        "Return a concise, three-line summary in this exact format:\n"
        "Olivia Smith: <score or No score found for Olivia Smith>\n"
        "Mia Anderson: <score or No score found for Mia Anderson>\n"
        "Mason Thompson: <score or No score found for Mason Thompson>\n"
        "File name: {}. File content: {}".format(target_file.filename, target_file.content),
        FeedbackScoresSummarySchema
    )
    result = extraction.summary

result