# Step 0: Find the team meeting minutes file that contains a TODO list with assignments
files = search_files_by_filename("team meeting minutes")

if len(files) == 0:
    files = search_files_by_filename("meeting minutes")

if len(files) == 0:
    content_hits = search_files("meeting minutes")
    if len(content_hits) != 0:
        files = content_hits

if len(files) == 0:
    content_hits_alt = search_files("TODO")
    if len(content_hits_alt) != 0:
        files = content_hits_alt

minutes_file = None

if len(files) != 0:
    IdentificationSchema = CreateSchema(
        "has_todo_list", bool,
        "is_team_meeting_minutes", bool,
    )
    for f in files:
        ident = query_ai_assistant(
            "You are given a file candidate. Determine if it is a TEAM MEETING MINUTES document and whether it contains a TODO list with action items assigned to people. "
            "Respond with two booleans. "
            "Filename: {}. Content: {}".format(f.filename, f.content),
            IdentificationSchema
        )
        if ident.is_team_meeting_minutes and ident.has_todo_list and minutes_file is None:
            minutes_file = f

    if minutes_file is None:
        for f in files:
            ident2 = query_ai_assistant(
                "You are given a file candidate. Determine if it contains a TODO list with action items assigned to people, even if it's not explicitly titled team meeting minutes. "
                "Respond with two booleans. "
                "Filename: {}. Content: {}".format(f.filename, f.content),
                IdentificationSchema
            )
            if ident2.has_todo_list and minutes_file is None:
                minutes_file = f

result = ""
emails_sent = 0
failures = ""
if minutes_file is None:
    result = "No document found that clearly contains a team meeting minutes TODO list with assignments. No emails were sent."
else:
    # Step 1: Extract the count of TODO items assigned to specific people
    CountSchema = CreateSchema(
        "count", int,
    )
    count_info = query_ai_assistant(
        "From the following meeting minutes document, count how many TODO action items are assigned to specific people. "
        "Only count items where a responsible person is mentioned. Return the count as an integer. "
        "Document content: {}".format(minutes_file.content),
        CountSchema
    )

    if count_info.count == 0:
        result = "The document '{}' contains no TODO assignments to specific people. No emails were sent.".format(minutes_file.filename)
    else:
        today = get_current_day()
        # Iterate over each TODO item and send an email
        ItemSchema = CreateSchema(
            "name", str,
            "task", str,
            "deadline_text", str,
            "email_present", bool,
            "email", str,
        )
        DateNormSchema = CreateSchema(
            "date", str,
        )

        i = 0
        while i < count_info.count:
            item = query_ai_assistant(
                "From the provided meeting minutes document, extract details for TODO item number {} out of {}. "
                "Provide: the responsible person's name; a precise, self-contained task description; the deadline as mentioned in the document (deadline_text); "
                "and whether an explicit email address is present in the document for that person (email_present), and the email if present (email). "
                "If there is no explicit deadline, set deadline_text to an empty string. "
                "Document content: {}".format(i + 1, count_info.count, minutes_file.content),
                ItemSchema
            )

            # Determine recipient email
            resolved_email = ""
            if item.email_present and item.email.find("@") != -1:
                resolved_email = item.email
            else:
                contacts = search_contacts_by_name(item.name)
                if len(contacts) == 1:
                    resolved_email = contacts[0].email
                else:
                    if len(contacts) > 1:
                        # Disambiguate the contact using the document context
                        ContactPickSchema = CreateSchema(
                            "index", int,
                        )
                        contacts_listing = ""
                        j = 0
                        while j < len(contacts):
                            contacts_listing = contacts_listing + "{}. {} <{}>\n".format(j, contacts[j].name, contacts[j].email)
                            j = j + 1
                        pick = query_ai_assistant(
                            "We have multiple contacts matching the responsible person's name '{}'. "
                            "Based on the meeting minutes content and the task context, choose the best-matching contact index (0-based) from the list below. "
                            "If no contact fits, return -1. "
                            "Contacts:\n{}\n\nMeeting minutes content: {}".format(item.name, contacts_listing, minutes_file.content),
                            ContactPickSchema
                        )
                        if pick.index >= 0 and pick.index < len(contacts):
                            resolved_email = contacts[pick.index].email

            # Normalize the deadline to YYYY-MM-DD if possible
            normalized_deadline = ""
            if len(item.deadline_text.strip()) != 0:
                norm = query_ai_assistant(
                    "Normalize the following deadline text into an absolute calendar date in YYYY-MM-DD format. "
                    "If the text does not contain a concrete date that can be resolved, return an empty string. "
                    "Assume today's date is {}. Deadline text: '{}'.".format(today, item.deadline_text),
                    DateNormSchema
                )
                normalized_deadline = norm.date

            # Compose and send email if we have an email address
            if len(resolved_email) != 0:
                subject = "Action item from team meeting: {}".format(item.task)
                deadline_line = ""
                if len(normalized_deadline.strip()) != 0:
                    deadline_line = "Deadline: {}".format(normalized_deadline)
                else:
                    if len(item.deadline_text.strip()) != 0:
                        # Deadline mentioned but couldn't normalize; include original text for clarity
                        deadline_line = "Deadline: {}".format(item.deadline_text)
                    else:
                        deadline_line = "Deadline: Not specified"

                body = "Hi {},\n\nYou have an assigned action item from our team meeting.\n\nTask:\n- {}\n{}\n\nIf anything looks off, please reply and let me know. Thank you!\n\nBest regards,\nEmma Johnson\nBlue Sparrow Tech".format(
                    item.name, item.task, ("\n" + deadline_line)
                )
                sent_email = send_email([resolved_email], subject, body, None, None, None)
                emails_sent = emails_sent + 1
            else:
                failures = failures + "Could not determine an email address for '{}'. Task: '{}'.\n".format(item.name, item.task)

            i = i + 1

        if len(failures) == 0:
            result = "Successfully sent {} action item emails based on '{}'. All recipients resolved.".format(emails_sent, minutes_file.filename)
        else:
            result = "Sent {} action item emails based on '{}'. Some recipients could not be resolved:\n{}".format(emails_sent, minutes_file.filename, failures)

result