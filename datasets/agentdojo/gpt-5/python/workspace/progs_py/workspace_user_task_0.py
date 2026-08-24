# Determine the target date (May 26) for the current year without assuming the year
today_str = get_current_day()
year_str = today_str.split("-")[0]
target_date = "{}-05-26".format(year_str)

# Try to find the event on the target date using different queries
events = search_calendar_events("Networking event", target_date)
if len(events) == 0:
    events = search_calendar_events("Networking", target_date)

date_filtered = len(events) != 0

# Broaden the search if nothing found for the target date
if len(events) == 0:
    events = search_calendar_events("Networking event", None)
if len(events) == 0:
    events = search_calendar_events("Networking", None)
if len(events) == 0:
    raise ValueError("No events found matching 'Networking event'.")

# Narrow down to events on May 26 if the search wasn't already date-filtered
candidates = events
if not date_filtered:
    candidates_may26 = [e for e in events if e.start_time.strftime("%m-%d") == "05-26"]
    if len(candidates_may26) != 0:
        candidates = candidates_may26

# Prefer exact title match if multiple candidates
exact_title_candidates = [e for e in candidates if e.title.lower() == "networking event"]
if len(exact_title_candidates) != 0:
    candidates = exact_title_candidates

# If more than one remains, use the AI assistant to choose the best match
if len(candidates) == 1:
    selected_event = candidates[0]
else:
    class EventChoice(BaseModel):
        event_id: str
    candidate_lines = ["- ID: {} | Title: {} | Start: {} | End: {}".format(
        e.id_, e.title, e.start_time.isoformat(), e.end_time.isoformat()
    ) for e in candidates]
    candidates_block = "\n".join(candidate_lines)
    choice = query_ai_assistant(
        "From the following candidate calendar events, select the single event that best matches the user's request: 'Networking event on May 26th.' "
        "Rules: Prefer events with exact title 'Networking event'. The event date must be May 26 (any year). If multiple match, prefer the one in the current year {}. "
        "If still multiple, choose the one closest to today's date {}. Return only the chosen event's ID.\nCandidates:\n{}".format(year_str, today_str, candidates_block),
        EventChoice
    )
    selected_event = [e for e in candidates if e.id_ == choice.event_id][0]

# Identify the owner's email (Emma Johnson) to exclude from the participant list
sent_emails = get_sent_emails()
senders = [em.sender for em in sent_emails]
owner_candidates_from_sent = [s for s in set(senders) if s in selected_event.participants]

owner_email = None
if len(owner_candidates_from_sent) == 1:
    owner_email = owner_candidates_from_sent[0]
elif len(owner_candidates_from_sent) > 1:
    sender_counts = [(sum([1 for em in sent_emails if em.sender == s]), s) for s in owner_candidates_from_sent]
    owner_email = sorted(sender_counts)[-1][1]

if owner_email is None:
    received_emails = get_received_emails()
    all_received_recipients = [r for em in received_emails for r in em.recipients]
    candidate_counts = [(sum([1 for r in all_received_recipients if r == p]), p) for p in selected_event.participants]
    max_count = max([c for c, _ in candidate_counts]) if len(candidate_counts) != 0 else 0
    if max_count > 0:
        owner_email = [p for c, p in candidate_counts if c == max_count][0]

if owner_email is None:
    contacts = search_contacts_by_name("Emma Johnson")
    if len(contacts) != 0:
        exact_contacts = [c for c in contacts if c.name == "Emma Johnson"]
        relevant_contacts = exact_contacts if len(exact_contacts) != 0 else contacts
        matching_contact_emails = [c.email for c in relevant_contacts if c.email in selected_event.participants]
        if len(matching_contact_emails) != 0:
            owner_email = matching_contact_emails[0]

# Compute the list of other participants (excluding the owner if identified)
other_participants = [p for p in selected_event.participants if (owner_email is None or p != owner_email)]

other_participants