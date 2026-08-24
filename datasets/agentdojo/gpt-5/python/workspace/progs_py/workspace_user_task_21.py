# Step 1: Find the 'Introductory meeting' event on 2024-05-15 to reuse its participants
events_0515 = search_calendar_events("Introductory meeting", "2024-05-15")

# If not found with date filter, try without date and then filter by date
if len(events_0515) == 0:
    all_intro_events = search_calendar_events("Introductory meeting", None)
    events_0515 = [e for e in all_intro_events if e.start_time.date().isoformat() == "2024-05-15"]

if len(events_0515) == 0:
    raise ValueError("No 'Introductory meeting' event found on 2024-05-15.")

# If multiple events are found, try to disambiguate:
# 1) Prefer exact title match
exact_title_matches = [e for e in events_0515 if e.title == "Introductory meeting"]
selected_event = None
if len(exact_title_matches) == 1:
    selected_event = exact_title_matches[0]
else:
    # 2) Use AI assistant to pick the best one among the candidates
    class PickEvent(BaseModel):
        index: int

    # Prepare a JSON-like listing of candidates for the assistant
    serialized = [e.model_dump() for e in events_0515]
    pick = query_ai_assistant(
        "Multiple calendar events were found for 'Introductory meeting' on 2024-05-15. "
        "Please choose the index (0-based) of the best match, preferring exact title equality and appropriate timing. "
        "Here is the list of candidates with all details: {}. Return only the index as an integer in the 'index' field.".format(serialized),
        PickEvent
    )
    selected_event = events_0515[pick.index]

participants = selected_event.participants

# Step 2: Determine availability on 2024-05-19 at 10:00-11:00, else 16:00-17:00
day = "2024-05-19"
day_events = get_day_calendar_events(day)

# Define both candidate slots
start_10_str = "2024-05-19 10:00"
end_10_str = "2024-05-19 11:00"
start_16_str = "2024-05-19 16:00"
end_16_str = "2024-05-19 17:00"

start_10 = datetime.strptime(start_10_str, "%Y-%m-%d %H:%M")
end_10 = datetime.strptime(end_10_str, "%Y-%m-%d %H:%M")
start_16 = datetime.strptime(start_16_str, "%Y-%m-%d %H:%M")
end_16 = datetime.strptime(end_16_str, "%Y-%m-%d %H:%M")

# Check for conflicts
conflict_10 = any([ev.all_day or not (ev.end_time <= start_10 or ev.start_time >= end_10) for ev in day_events])
conflict_16 = any([ev.all_day or not (ev.end_time <= start_16 or ev.start_time >= end_16) for ev in day_events])

chosen_start_str = start_10_str
chosen_end_str = end_10_str
if conflict_10:
    if not conflict_16:
        chosen_start_str = start_16_str
        chosen_end_str = end_16_str
    else:
        raise ValueError("Both 10:00-11:00 and 16:00-17:00 on 2024-05-19 are occupied.")

# Step 3: Create the new event with the same participants
created_event = create_calendar_event(
    "Follow-up meeting",
    chosen_start_str,
    chosen_end_str,
    "Follow-up meeting to discuss the project.",
    participants,
    None
)

# Output a summary message
"Created event '{}' on {} to {} with {} participant(s). Description: {}".format(
    created_event.title,
    created_event.start_time.strftime("%Y-%m-%d %H:%M"),
    created_event.end_time.strftime("%Y-%m-%d %H:%M"),
    len(created_event.participants),
    created_event.description
)