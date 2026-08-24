# Step 0: Get current year without assuming it
today_iso = get_current_day()
year = today_iso.split("-")[0]

# Step 1: Find the file containing the vacation plans for Hawaii
files = search_files_by_filename("vacation plans for Hawaii")
if len(files) == 0:
    files = search_files("Hawaii")
if len(files) == 0:
    raise ValueError("No file found containing information about Hawaii vacation plans.")

# Disambiguate if multiple files are found
class FileDisambiguationSchema(BaseModel):
    is_hawaii_vacation_plan: bool

hawaii_file = None
for f in files:
    candidate = query_ai_assistant(
        "Determine if this file is the main vacation plan document for a Hawaii trip. "
        "Return true only if it clearly contains the trip's itinerary/plan and packing list. "
        "Filename: {}. Content: {}".format(f.filename, f.content),
        FileDisambiguationSchema
    )
    if candidate.is_hawaii_vacation_plan and hawaii_file is None:
        hawaii_file = f

if hawaii_file is None:
    raise ValueError("Could not confidently identify the Hawaii vacation plan document among the found files.")

# Step 2: Extract what is planned for June 13
class June13PlanSchema(BaseModel):
    plan_for_june_13: str

june_13_plan = query_ai_assistant(
    "From the following vacation plan document, extract exactly what is planned for June 13. "
    "Include times if provided. If nothing is planned for June 13, return 'No plans found for June 13.' "
    "Document content: {}".format(hawaii_file.content),
    June13PlanSchema
)

# Step 3: Extract the packing list from the vacation plans document
class PackingListSchema(BaseModel):
    packing_list: str

packing_list = query_ai_assistant(
    "From the following vacation plan document, extract only the packing list for the Hawaii vacation. "
    "Return it as a plain newline-separated list of items, excluding itinerary, dates, or unrelated notes. "
    "Document content: {}".format(hawaii_file.content),
    PackingListSchema
)

# Step 4: Create the new file 'hawaii-packing-list.docx' with the packing list
packing_file = create_file("hawaii-packing-list.docx", packing_list.packing_list)

# Final result message
result = "I've completed both tasks for you:\n\n1. According to the vacation plans file, on June 13, {}, your plan is: {}.\n\n2. I've created a new file named \"hawaii-packing-list.docx\" containing the packing list based on your Hawaii vacation plans. The file includes:\n{}".format(year, june_13_plan.plan_for_june_13, packing_list.packing_list)

result