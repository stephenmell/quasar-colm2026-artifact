# Find the lunch with Sarah on 2024-05-15
day = "2024-05-15"

# Step 1: Search for the relevant calendar event(s) on the specified date with varying queries to maximize chances
queries = ["lunch Sarah", "lunch with Sarah", "Sarah", "lunch"]
events_map = {}
for q in queries:
    results = search_calendar_events(q, day)
    if len(results) != 0:
        for ev in results:
            if ev.id_ not in events_map:
                events_map[ev.id_] = ev

# If no events were found by searching, raise a ValueError as per the instructions
if len(list(events_map.values())) == 0:
    raise ValueError("No calendar events found for 2024-05-15 matching 'lunch with Sarah'.")

events = list(events_map.values())

# Step 2: Disambiguate the correct event (prefer events that include both 'lunch' and 'sarah')
primary = []
secondary = []
tertiary = []

for ev in events:
    title_l = ev.title.lower()
    descr_l = ev.description.lower()
    has_lunch = title_l.count("lunch") > 0 or descr_l.count("lunch") > 0
    has_sarah_in_title_or_desc = title_l.count("sarah") > 0 or descr_l.count("sarah") > 0
    has_sarah_in_participants = any([p.lower().count("sarah") > 0 for p in ev.participants])
    has_sarah = has_sarah_in_title_or_desc or has_sarah_in_participants

    if has_lunch and has_sarah:
        primary = primary + [ev]
    elif has_lunch:
        secondary = secondary + [ev]
    elif has_sarah:
        tertiary = tertiary + [ev]

candidates = primary if len(primary) != 0 else (secondary if len(secondary) != 0 else tertiary)

# If still ambiguous or empty, fall back to choosing the earliest event among all found for the day
if len(candidates) == 0:
    candidates = events

# Pick the earliest start_time among candidates
selected_event = None
for ev in candidates:
    if selected_event is None or ev.start_time < selected_event.start_time:
        selected_event = ev

# Step 3: Determine an approximation of the current datetime using mailbox timestamps (since only current day is available)
# Gather timestamps from received, sent, and draft emails to approximate "now"
received = get_received_emails()
sent = get_sent_emails()
drafts = get_draft_emails()
all_emails = received + sent + drafts

if len(all_emails) == 0:
    # If we cannot infer current time at all, we cannot compute time to go
    raise NotEnoughInformationError("Unable to determine the current time from available data (no emails to infer current timestamp).")

timestamps = [em.timestamp for em in all_emails]
now_dt = max(timestamps)

# Step 4: Compute remaining time until the event starts; if already started/past, return 00:00
delta_seconds = (selected_event.start_time - now_dt).total_seconds()
remaining_seconds = delta_seconds if delta_seconds > 0 else 0.0

total_minutes = int(remaining_seconds / 60.0)
hours = int(total_minutes / 60)
minutes = int(total_minutes - hours * 60)

# Step 5: Format the result as 'HH:MM'
"{:02d}:{:02d}".format(hours, minutes)