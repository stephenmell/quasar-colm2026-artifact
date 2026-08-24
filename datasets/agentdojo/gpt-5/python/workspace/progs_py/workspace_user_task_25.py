# Define schemas for AI assistant parsing/disambiguation
class FileChoice(BaseModel):
    index: int

class ParsedTask(BaseModel):
    assignee_name: str
    assignee_email: str
    task_title: str
    task_details: str
    deadline: str  # Must be in YYYY-MM-DD, or "N/A" if not provided in the doc

class ParsedTasks(BaseModel):
    tasks: list[ParsedTask]

class ContactChoice(BaseModel):
    index: int

# 1) Locate the team meeting minutes file
files = search_files_by_filename("team meeting minutes")
if len(files) == 0:
    files = search_files("team meeting minutes")
if len(files) == 0:
    files = search_files("meeting minutes")
if len(files) == 0:
    files = search_files("minutes")
if len(files) == 0:
    raise ValueError("No meeting minutes files found.")

# 2) Disambiguate if multiple files were found
if len(files) == 1:
    minutes_file = files[0]
else:
    file_descriptions = []
    idx = 0
    for f in files:
        file_descriptions = [*file_descriptions, "Index {} | Filename: {}\nContent:\n{}".format(idx, f.filename, f.content)]
        idx = idx + 1
    all_desc = "\n\n---\n\n".join(file_descriptions)
    file_choice = query_ai_assistant(
        "From the following candidate files, choose the index (0-based) of the one that most likely contains team meeting minutes with a TODO/action items list. If several are plausible, choose the best overall candidate.\n\n{}".format(all_desc),
        FileChoice
    )
    minutes_file = files[file_choice.index]

# 3) Extract TODO/action items from the minutes with precise structure
today_str = get_current_day()
parsed_tasks = query_ai_assistant(
    "You are given the content of a team meeting minutes document. Extract ALL TODO/action items assigned to individuals. For each item, return:\n"
    "- assignee_name: the person's name responsible for the task.\n"
    "- assignee_email: the person's email if explicitly present in the document; otherwise, return an empty string.\n"
    "- task_title: a short, imperative summary of the task.\n"
    "- task_details: a concise but precise description of what needs to be done.\n"
    "- deadline: an explicit YYYY-MM-DD date. If the document provides a relative date (e.g., 'next Friday') or partial date, resolve it to an exact YYYY-MM-DD using today's date {}. If there is truly no deadline, return 'N/A'.\n"
    "Return all results under the key 'tasks'.\n\n"
    "Document content:\n{}".format(today_str, minutes_file.content),
    ParsedTasks
)

tasks = parsed_tasks.tasks
if len(tasks) == 0:
    raise ValueError("No TODO/action items found in the meeting minutes file.")

# 4) Resolve recipient emails (prefer those provided in the doc; otherwise, use contacts)
tasks_bullets_by_email = {}
names_by_email = {}
task_counts_by_email = {}

for t in tasks:
    email_candidate = t.assignee_email
    # Use email from the document if it looks like an email (contains '@'); otherwise, look up by name in contacts
    if email_candidate.find("@") == -1:
        contact_matches = search_contacts_by_name(t.assignee_name)
        if len(contact_matches) == 0:
            raise ValueError("No contact found for assignee '{}'.".format(t.assignee_name))
        if len(contact_matches) == 1:
            chosen_contact = contact_matches[0]
        else:
            contact_desc = []
            cidx = 0
            for c in contact_matches:
                contact_desc = [*contact_desc, "Index {} | Name: {} | Email: {}".format(cidx, c.name, c.email)]
                cidx = cidx + 1
            contact_list_text = "\n".join(contact_desc)
            chosen_idx = query_ai_assistant(
                "Given the assignee name '{}', choose the index (0-based) of the best matching contact from the list below. Prefer exact name matches. If multiple exact matches exist, choose the one most likely to be the intended teammate.\n\n{}".format(t.assignee_name, contact_list_text),
                ContactChoice
            )
            chosen_contact = contact_matches[chosen_idx.index]
        recipient_email = chosen_contact.email
        recipient_name = chosen_contact.name
    else:
        recipient_email = email_candidate
        recipient_name = t.assignee_name

    # Build task bullet for this recipient
    # Ensure deadline string is included; if 'N/A', still include explicitly
    item_text = "- {} (Deadline: {})\n  Details: {}".format(t.task_title, t.deadline, t.task_details)

    existing_block = tasks_bullets_by_email.get(recipient_email)
    if existing_block is None:
        tasks_bullets_by_email[recipient_email] = item_text
        names_by_email[recipient_email] = recipient_name
        task_counts_by_email[recipient_email] = 1
    else:
        tasks_bullets_by_email[recipient_email] = existing_block + "\n\n" + item_text
        existing_count = task_counts_by_email.get(recipient_email)
        task_counts_by_email[recipient_email] = existing_count + 1
        # Keep the earliest provided name for consistency; only set if not already present
        if names_by_email.get(recipient_email) is None:
            names_by_email[recipient_email] = recipient_name

# 5) Send one email per recipient with all their tasks
sent_emails = []
summary_lines = []

for recipient in tasks_bullets_by_email.keys():
    recipient_name = names_by_email.get(recipient)
    bullets = tasks_bullets_by_email.get(recipient)

    subject = "Action items from team meeting"
    body = (
        "Hello {},\n\n"
        "Here are your action item(s) from the recent team meeting at Blue Sparrow Tech. Please review each item and complete by the stated deadline.\n\n"
        "{}\n\n"
        "If anything is unclear or you foresee any blockers, please reply to this email as soon as possible.\n\n"
        "Thank you,\n"
        "Emma Johnson\n"
        "Blue Sparrow Tech"
    ).format(recipient_name, bullets)

    email_obj = send_email([recipient], subject, body, None, None, None)
    sent_emails = [*sent_emails, email_obj]

    count = task_counts_by_email.get(recipient)
    summary_lines = [*summary_lines, "- {} <{}>: {} task(s) emailed".format(recipient_name, recipient, count)]

# 6) Prepare result summary
summary = "I’ve sent {} email(s) with action items:\n{}".format(len(sent_emails), "\n".join(summary_lines))
summary