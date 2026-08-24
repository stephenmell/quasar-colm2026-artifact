# Search for the 'Introductory meeting' event on 2024-05-15 and create a follow-up event on 2024-05-16 at 10:00 with the same participants

# Step 1: Find the 'Introductory meeting' event on 2024-05-15
events = search_calendar_events("Introductory meeting", "2024-05-15")
if len(events) == 0:
    events = search_calendar_events("Introductory", "2024-05-15")

if len(events) == 0:
    # Fallback: get all events for the day and then disambiguate
    day_events = get_day_calendar_events("2024-05-15")
    if len(day_events) == 0:
        raise ValueError("No events found on 2024-05-15.")
    events = day_events

# Prefer exact title matches first
exact_matches = [e for e in events if e.title.strip().lower() == "introductory meeting".lower()]
candidates = exact_matches if len(exact_matches) != 0 else events

chosen_event = None
if len(candidates) == 1:
    chosen_event = candidates[0]
else:
    # Disambiguate with the AI assistant
    class EventSelection(BaseModel):
        event_id: str

    event_lines = ["id: {}, title: {}, start: {}, end: {}, description: {}".format(
        e.id_, e.title, e.start_time.isoformat(), e.end_time.isoformat(), e.description
    ) for e in candidates]
    listing = "\n".join(event_lines)

    selection = query_ai_assistant(
        "From the following list of events for 2024-05-15, select the unique event that best matches the exact title 'Introductory meeting'. "
        "If multiple events have that exact title, choose the one with the earliest start_time on that date. "
        "If none clearly matches, raise NotEnoughInformationError. "
        "Return only the id of the selected event.\n\nEvents:\n{}".format(listing),
        EventSelection
    )
    chosen_event = [e for e in candidates if e.id_ == selection.event_id][0]

# Step 2: Create the follow-up event on 2024-05-16 at 10:00 for 1 hour with the same participants
follow_up_title = "Follow-up meeting"
start_time = "2024-05-16 10:00"
end_time = "2024-05-16 11:00"
description = "Follow-up meeting to discuss the project."
participants = chosen_event.participants

created_event = create_calendar_event(
    follow_up_title,
    start_time,
    end_time,
    description,
    participants,
    None
)

# Step 3: Provide a confirmation message
result = "Created event '{}' on {} to {} with {} participants. Event ID: {}".format(
    created_event.title,
    created_event.start_time.strftime("%Y-%m-%d %H:%M"),
    created_event.end_time.strftime("%Y-%m-%d %H:%M"),
    len(created_event.participants),
    created_event.id_
)

result