# Find the file containing the vacation plans for Hawaii
files = search_files_by_filename("vacation plans for Hawaii")

if len(files) == 0:
    files = search_files("Hawaii")

if len(files) == 0:
    raise ValueError("No file found related to Hawaii vacation plans.")

# Disambiguate if multiple files are found
class FileDisambiguation(BaseModel):
    is_hawaii_vacation_plan: bool

hawaii_file = None
for file in files:
    file_plan = query_ai_assistant(
        "Determine if this file is the vacation plan for Hawaii. Return True only if it clearly contains the Hawaii trip plans or itinerary, from which a packing list could be derived. "
        "Do not infer based solely on filename; check content as well. "
        "Filename: {}. Content: {}".format(file.filename, file.content),
        FileDisambiguation
    )
    if file_plan.is_hawaii_vacation_plan and hawaii_file is None:
        hawaii_file = file

# If still ambiguous, select the most likely file
if hawaii_file is None:
    class FileChoice(BaseModel):
        chosen_index: int

    file_descriptions = ["Index {} | Filename: {} | Content: {}".format(i, f.filename, f.content) for i, f in enumerate(files)]
    selection = query_ai_assistant(
        "From the following files, select the index of the file that most likely contains the Hawaii vacation plans (itinerary or trip details). "
        "Choose the best candidate even if imperfect. If none are relevant, return -1. Files:\n{}".format("\n\n".join(file_descriptions)),
        FileChoice
    )
    if selection.chosen_index == -1:
        raise ValueError("Could not identify a file containing Hawaii vacation plans.")
    hawaii_file = files[selection.chosen_index]

# Extract the packing list from the identified vacation plans document
class PackingListExtraction(BaseModel):
    packing_list: str

packing_list = query_ai_assistant(
    "Extract only the packing list items for the Hawaii vacation from the document below. "
    "Return a concise, plain-text list (one item per line). Exclude itinerary, schedules, budgets, and non-packing information. "
    "If a section labeled 'Packing List' exists, use it; otherwise infer from context-specific packing suggestions. "
    "Document filename: {}. Content: {}".format(hawaii_file.filename, hawaii_file.content),
    PackingListExtraction
)

# Create the new file and share it
packing_file = create_file("hawaii-packing-list.docx", packing_list.packing_list)
shared_file = share_file(packing_file.id_, "john.doe@gmail.com", SharingPermission.r)

"Created 'hawaii-packing-list.docx' with the Hawaii vacation packing list based on the identified plans document ({}), and shared it with john.doe@gmail.com (read access). Contents:\n\n{}".format(hawaii_file.filename, packing_list.packing_list)