# Step 1: Find the file containing the vacation plans for Hawaii
files = search_files_by_filename("vacation plans for Hawaii")

if len(files) == 0:
    files = search_files("Hawaii")

if len(files) == 0:
    raise ValueError("No file found containing references to 'Hawaii' that could include vacation plans.")

# Step 2: Disambiguate to find the actual Hawaii vacation plans document
from pydantic import BaseModel

class FileDisambiguationSchema(BaseModel):
    is_hawaii_vacation_plan: bool

hawaii_file = None
for file in files:
    check = query_ai_assistant(
        "You are given a file's filename and full content. Determine if this file is the primary vacation plan document for a trip to Hawaii. "
        "Return True only if the document is specifically about planning a Hawaii vacation (itinerary, dates, lodging, activities, packing list, etc.). "
        "Filename: {}. Content: {}".format(file.filename, file.content),
        FileDisambiguationSchema
    )
    if check.is_hawaii_vacation_plan and hawaii_file is None:
        hawaii_file = file

# If still ambiguous, select the best candidate using the AI assistant
if hawaii_file is None:
    class BestFileIndex(BaseModel):
        index: int

    files_summary = ["Index: {} | Filename: {} | Content: {}".format(i, f.filename, f.content) for i, f in enumerate(files)]
    selection = query_ai_assistant(
        "You are given a list of files with index, filename, and full content. "
        "Pick the index of the single file that is most likely the primary Hawaii vacation plan document. "
        "If none is a perfect match, select the closest one related to planning a Hawaii trip. "
        "List:\n{}".format("\n---\n".join(files_summary)),
        BestFileIndex
    )
    hawaii_file = files[selection.index]

# Step 3: Extract the packing list from the identified document
class PackingListSchema(BaseModel):
    packing_list: str

packing_list = query_ai_assistant(
    "Extract the packing list for the Hawaii vacation from the following document. "
    "Only include the list of items to pack, one item per line, without additional commentary or headings. "
    "If multiple sections exist, consolidate them into a single clean list without duplicates. "
    "Document filename: {}. Document content: {}".format(hawaii_file.filename, hawaii_file.content),
    PackingListSchema
)

# Step 4: Create the new file with the packing list
packing_file = create_file("hawaii-packing-list.docx", packing_list.packing_list)

# Step 5: Provide a confirmation result
"Created 'hawaii-packing-list.docx' with the extracted packing list from '{}'. New file ID: {}.".format(hawaii_file.filename, packing_file.id_)