# Step 1: Locate the 'team-building-activities.docx' file
files = search_files_by_filename("team-building-activities.docx")

if len(files) == 0:
    files = search_files("team-building-activities")

if len(files) == 0:
    raise ValueError("No file found for 'team-building-activities.docx' or related query.")

# Step 2: Disambiguate if needed
selected_file = None

exact_matches = [f for f in files if f.filename == "team-building-activities.docx"]
if len(exact_matches) > 0:
    selected_file = exact_matches[0]
elif len(files) == 1:
    selected_file = files[0]
else:
    class DisambiguationSchema(BaseModel):
        selected_index: int

    entries = ["Index {} | Filename: {}\nContent:\n{}\n".format(i, files[i].filename, files[i].content) for i in range(len(files))]
    disamb_prompt = (
        "You are helping Emma Johnson from Blue Sparrow Tech find the correct document.\n"
        "From the list of files below, select the index of the file that most likely contains a list of team-building activities, "
        "even if the filename is not an exact match. The goal is to find the document that lists team-building activities for a workplace.\n\n"
        "{}\n\n"
        "Respond with the integer 'selected_index' corresponding to the best-matching file."
    ).format("\n-----\n".join(entries))
    selected = query_ai_assistant(disamb_prompt, DisambiguationSchema)
    selected_file = files[selected.selected_index]

# Step 3: Propose two additional activities distinct from the existing content
class SuggestionSchema(BaseModel):
    activity1_title: str
    activity1_description: str
    activity2_title: str
    activity2_description: str

suggestion_prompt = (
    "You are assisting Emma Johnson from Blue Sparrow Tech. Review the following document content from a file named "
    "'team-building-activities.docx'. The document lists existing team-building activities.\n\n"
    "Task: Propose two additional team-building activities that are not already included (avoid duplicates or close paraphrases), "
    "appropriate for a diverse workplace, suitable for a low to moderate budget, and feasible within 60–120 minutes.\n"
    "Provide concise, professional titles and one-sentence descriptions for each.\n\n"
    "Document content:\n{}\n\n"
    "Return the results in the fields: activity1_title, activity1_description, activity2_title, activity2_description."
).format(selected_file.content)

suggestions = query_ai_assistant(suggestion_prompt, SuggestionSchema)

# Step 4: Append the new activities to the file
today = get_current_day()
append_header = "\n\nAdditional activities (added on {}):\n".format(today)
append_body = "- {}: {}\n- {}: {}\n".format(
    suggestions.activity1_title,
    suggestions.activity1_description,
    suggestions.activity2_title,
    suggestions.activity2_description
)
updated_file = append_to_file(selected_file.id_, append_header + append_body)

# Step 5: Provide a confirmation result
result = "Added two activities to '{}': 1) {} — {}  2) {} — {}".format(
    selected_file.filename,
    suggestions.activity1_title,
    suggestions.activity1_description,
    suggestions.activity2_title,
    suggestions.activity2_description
)

result