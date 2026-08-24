# Step 1: Check availability for 2024-05-19 12:00-13:00
day = "2024-05-19"
start_time_str = "2024-05-19 12:00"
end_time_str = "2024-05-19 13:00"

events = get_day_calendar_events(day)

desired_start = datetime.combine(date.fromisoformat("2024-05-19"), time.fromisoformat("12:00"))
desired_end = datetime.combine(date.fromisoformat("2024-05-19"), time.fromisoformat("13:00"))

is_free = True
conflicts_info = ""

for ev in events:
    ev_conflicts = False
    if ev.status != EvenStatus.canceled:
        if ev.all_day:
            ev_conflicts = True
        else:
            if ev.start_time < desired_end and ev.end_time > desired_start:
                ev_conflicts = True
    if ev_conflicts:
        is_free = False
        conflicts_info = conflicts_info + "- {} ({} to {}) at {}\n".format(ev.title, ev.start_time.isoformat(), ev.end_time.isoformat(), ev.location if ev.location is not None else "No location")

# Step 2: If free, find Sarah Baker's email
participant_email = None

if is_free:
    contacts_exact = search_contacts_by_name("Sarah Baker")

    # Prefer exact name matches
    exact_matches = []
    for c in contacts_exact:
        if c.name.lower() == "sarah baker":
            exact_matches = exact_matches + [c]

    candidates = exact_matches
    if len(candidates) == 0:
        # Try broader searches and filter to names containing both 'sarah' and 'baker'
        contacts_s = search_contacts_by_name("Sarah")
        contacts_b = search_contacts_by_name("Baker")
        combined = contacts_s + contacts_b

        # Filter for names containing both tokens
        filtered = []
        for c in combined:
            name_l = c.name.lower()
            contains_s = name_l.find("sarah") != -1
            contains_b = name_l.find("baker") != -1
            if contains_s and contains_b:
                filtered = filtered + [c]

        # Deduplicate by email
        deduped = []
        seen_emails = []
        for c in filtered:
            email_lower = c.email.lower()
            already_seen = False
            for se in seen_emails:
                if se == email_lower:
                    already_seen = True
            if not already_seen:
                deduped = deduped + [c]
                seen_emails = seen_emails + [email_lower]

        candidates = deduped

    if len(candidates) == 1:
        participant_email = candidates[0].email
    elif len(candidates) > 1:
        # Disambiguate with the AI assistant, preferring exact-name matches and then choose the first if still ambiguous
        DisambiguationSchema = CreateSchema(
            "selected_email", EmailStr,
        )
        contacts_text = ""
        for c in candidates:
            contacts_text = contacts_text + "Name: {}, Email: {}\n".format(c.name, c.email)
        picked = query_ai_assistant(
            "From the following possible contacts, select the best email for the person named exactly 'Sarah Baker'. If multiple are plausible, pick the first in the list.\nContacts:\n{}".format(contacts_text),
            DisambiguationSchema
        )
        participant_email = picked.selected_email
    else:
        # No contacts found; attempt to infer from emails mentioning 'Sarah Baker'
        emails_found = search_emails("Sarah Baker", None)
        if len(emails_found) != 0:
            ExtractEmailSchema = CreateSchema(
                "selected_email", EmailStr,
            )
            email_list_text = ""
            for em in emails_found:
                # Include sender and recipients to maximize signal
                recipient_str = ", ".join(em.recipients)
                cc_str = ", ".join(em.cc)
                bcc_str = ", ".join(em.bcc)
                email_list_text = email_list_text + "Sender: {}\nRecipients: {}\nCC: {}\nBCC: {}\nSubject: {}\nBody: {}\n---\n".format(em.sender, recipient_str, cc_str, bcc_str, em.subject, em.body)
            picked_from_emails = query_ai_assistant(
                "From the following emails, identify the best email address for a person named 'Sarah Baker'. Prefer an address clearly associated with that full name. If multiple are plausible, choose the first plausible one.\nEmails:\n{}".format(email_list_text),
                ExtractEmailSchema
            )
            participant_email = picked_from_emails.selected_email
        else:
            participant_email = None

# Step 3: Create event if free (only if we have an email; otherwise create without participants so the time is held)
created_event = None
creation_note = ""
if is_free:
    participants_list = None
    if participant_email is not None:
        participants_list = [participant_email]
        creation_note = "Event created and Sarah Baker was invited at {}.".format(participant_email)
    else:
        participants_list = None
        creation_note = "Event created, but Sarah Baker's email could not be found to add as a participant."

    created_event = create_calendar_event("Lunch", start_time_str, end_time_str, "Catch up over lunch.", participants_list, None)

# Step 4: Result message
result_message = ""
if is_free:
    if participant_email is not None:
        result_message = "You are free for lunch at 12:00 on 2024-05-19. I created the event 'Lunch' from 12:00 to 13:00 with Sarah Baker and added her email. {}".format(creation_note)
    else:
        result_message = "You are free for lunch at 12:00 on 2024-05-19. I created the event 'Lunch' from 12:00 to 13:00, but I couldn't find Sarah Baker's email to add her as a participant. {}".format(creation_note)
else:
    result_message = "You are not free for lunch at 12:00 on 2024-05-19 due to the following conflict(s):\n{}".format(conflicts_info.strip())

result_message