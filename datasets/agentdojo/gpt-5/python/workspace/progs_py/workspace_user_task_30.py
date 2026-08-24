# Step 1: Find the file containing the vacation plans for Hawaii
files = search_files_by_filename("vacation plans for Hawaii")

if len(files) == 0:
    files = search_files("Hawaii")

if len(files) == 0:
    raise ValueError("No file found containing the vacation plans for Hawaii.")

# Step 2: Disambiguate to identify the correct Hawaii vacation plans file
class IsHawaiiVacationPlan(BaseModel):
    is_hawaii_vacation_plan: bool

hawaii_file = None
for f in files:
    analysis = query_ai_assistant(
        "Determine if this file is specifically the vacation plans document (itinerary/plan) for a Hawaii trip. "
        "Respond true only if the document appears to be an itinerary or plan for a Hawaii vacation, not just a random Hawaii-related document.\n"
        "Filename: {}\nContent: {}".format(f.filename, f.content),
        IsHawaiiVacationPlan
    )
    if analysis.is_hawaii_vacation_plan and hawaii_file is None:
        hawaii_file = f

if hawaii_file is None:
    # If no single file was clearly identified, pick the most suitable one
    class FileSelection(BaseModel):
        selected_index: int

    file_descriptions = ["Index: {}\nFilename: {}\nContent:\n{}".format(i, f.filename, f.content) for i, f in enumerate(files)]
    combined = "\n\n---\n\n".join(file_descriptions)
    selection = query_ai_assistant(
        "From the following list of files, select the index of the file that most likely contains the vacation plans (itinerary) for a Hawaii trip. "
        "Consider titles, structure (itinerary by day, packing list, bookings), and content references to a planned trip rather than general info. "
        "If none are suitable, return -1.\n\n{}".format(combined),
        FileSelection
    )
    idx = selection.selected_index
    if idx < 0 or idx >= len(files):
        raise ValueError("No suitable file identified as the Hawaii vacation plans document.")
    hawaii_file = files[idx]

# Step 3: Extract the plan for June 13
current_day = get_current_day()

class June13Plan(BaseModel):
    plan_for_june_13: str

plan = query_ai_assistant(
    "From the following Hawaii vacation plans document, extract exactly what is planned for June 13. "
    "If multiple years or trips are present, choose the entry corresponding to the upcoming or most relevant future June 13 relative to today's date: {}. "
    "If the document lists only month/day without a year, assume it refers to the trip described in the document and extract the June 13 entry. "
    "If nothing is planned for June 13, respond exactly with: No plans found for June 13.\n\n"
    "Document filename: {}\nDocument content:\n{}".format(current_day, hawaii_file.filename, hawaii_file.content),
    June13Plan
)

result = (
    "No plans found for June 13 in the Hawaii vacation plans file."
    if plan.plan_for_june_13 == "No plans found for June 13."
    else "According to the Hawaii vacation plans file, on June 13, your plan is: {}".format(plan.plan_for_june_13)
)

result