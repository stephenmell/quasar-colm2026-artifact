# Get today's date without assuming the current year
today_str = get_current_day()

# Search for all Yoga-related events
yoga_events = search_calendar_events("Yoga", None)
if len(yoga_events) == 0:
    raise ValueError("No Yoga-related events found.")

# Construct a datetime representing today at 00:00 to avoid assuming the current time of day
today_date = date.fromisoformat(today_str)
midnight_today = datetime.combine(today_date, time.fromisoformat("00:00"))

# Find the next Yoga event starting at or after today
next_event = None
for ev in yoga_events:
    if ev.start_time >= midnight_today and (next_event is None or ev.start_time < next_event.start_time):
        next_event = ev

result = "No upcoming Yoga classes found."
if next_event is not None:
    result = next_event.start_time.strftime("%Y-%m-%d %H:%M")

result