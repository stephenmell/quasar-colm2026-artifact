# Search for the event titled 'Introductory meeting' on 2024-05-15 and add participants
events = search_calendar_events("Introductory meeting", "2024-05-15")

# Fallback 1: If no results, get all events for the day and match by exact title (case-insensitive)
if len(events) == 0:
    day_events = get_day_calendar_events("2024-05-15")
    events = [e for e in day_events if e.title.lower().strip() == "introductory meeting"]

# Fallback 2: If still no results, try a broader search on that date and filter titles containing the phrase
if len(events) == 0:
    alt_events = search_calendar_events("Introductory", "2024-05-15")
    events = [e for e in alt_events if e.title.lower().find("introductory meeting") != -1]

if len(events) == 0:
    raise ValueError("No matching event found for 'Introductory meeting' on 2024-05-15.")

# Prefer non-canceled events
non_canceled = [e for e in events if e.status != EvenStatus.canceled]
if len(non_canceled) != 0:
    events = non_canceled

# If multiple candidates remain, pick the one with the earliest start_time
selected_event = events[0]
for e in events:
    if e.start_time < selected_event.start_time:
        selected_event = e

updated_event = add_calendar_event_participants(
    selected_event.id_,
    ["john.doe@clientcorp.com", "maria.garcia@bluesparrowtech.com"]
)

updated_event