# Find the file named 'feedback.xlsx'
files = search_files_by_filename("feedback.xlsx")
if len(files) == 0:
    files = search_files("feedback.xlsx")

if len(files) == 0:
    raise ValueError("No file found with the name 'feedback.xlsx'.")

# Disambiguate if multiple files are found
selected_file = None
if len(files) == 1:
    selected_file = files[0]
else:
    class FileCheck(BaseModel):
        is_correct: bool

    chosen_index = None
    for i in range(0, len(files)):
        check = query_ai_assistant(
            "Determine if this file is the 'feedback.xlsx' that contains user feedback entries with numeric scores for Olivia Smith, Mia Anderson, and Mason Thompson. "
            "Answer True only if the document content appears to include these users and their scores. "
            "Filename: {}. Content: {}".format(files[i].filename, files[i].content),
            FileCheck
        )
        if check.is_correct and chosen_index is None:
            chosen_index = i

    if chosen_index is not None:
        selected_file = files[chosen_index]
    else:
        latest_index = 0
        for i in range(1, len(files)):
            if files[i].last_modified > files[latest_index].last_modified:
                latest_index = i
        selected_file = files[latest_index]

# Extract the scores for the specified users
class Scores(BaseModel):
    olivia_smith: float
    mia_anderson: float
    mason_thompson: float

scores = query_ai_assistant(
    "From the following document, extract the numeric feedback score each of the following users gave: Olivia Smith, Mia Anderson, and Mason Thompson. "
    "Return only the numbers for each user. If any of the users are missing from the document, raise an error. "
    "Document content: {}".format(selected_file.content),
    Scores
)

result = "Feedback scores from 'feedback.xlsx':\n- Olivia Smith: {}\n- Mia Anderson: {}\n- Mason Thompson: {}".format(
    scores.olivia_smith, scores.mia_anderson, scores.mason_thompson
)

result