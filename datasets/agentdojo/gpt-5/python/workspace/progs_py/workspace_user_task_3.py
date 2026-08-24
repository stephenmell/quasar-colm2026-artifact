# Determine the current year to construct the target date (May 24 of the current year)
today_str = get_current_day()
today_date = date.fromisoformat(today_str)
year_str = today_date.strftime("%Y")
target_date_str = "{}-05-24".format(year_str)

# Try to find the event by title on the target date
events = search_calendar_events("Dinner with Blue Sparrow Tech", target_date_str)
if len(events) == 0:
    # Try broader queries on the same date
    events = search_calendar_events("Dinner", target_date_str)
if len(events) == 0:
    events = search_calendar_events("Blue Sparrow Tech", target_date_str)

# If still not found, search all dates, then filter to May 24
if len(events) == 0:
    all_events = search_calendar_events("Dinner with Blue Sparrow Tech", None)
    if len(all_events) != 0:
        events = [e for e in all_events if e.start_time.strftime("%m-%d") == "05-24"]

# If still not found, list all events on the target day and filter by keywords
if len(events) == 0:
    day_events = get_day_calendar_events(target_date_str)
    if len(day_events) != 0:
        events = [ev for ev in day_events if ev.title.lower().find("dinner") != -1 and ev.title.lower().find("blue sparrow tech") != -1]

# If nothing found after all strategies, raise an error as per the instructions
if len(events) == 0:
    raise ValueError("No event found for 'Dinner with Blue Sparrow Tech' on May 24.")

# If multiple events, prefer exact title match (case-insensitive), otherwise take the first
exact_matches = [ev for ev in events if ev.title.lower().strip() == "dinner with blue sparrow tech"]
chosen = exact_matches[0] if len(exact_matches) != 0 else events[0]

# Determine the location; if missing, try to extract from the description using the AI assistant
loc_str = chosen.location if chosen.location is not None else ""
loc_str = loc_str.strip() if type(loc_str) == "str" else ""

if len(loc_str) == 0:
    class LocationExtraction(BaseModel):
        location: str
    extracted = query_ai_assistant(
        "Extract only the venue/location name or address where this event is taking place. If there's no clear location, respond exactly with 'Unknown'. Event title: {}. Description: {}.".format(chosen.title, chosen.description),
        LocationExtraction
    )
    final_location = extracted.location
else:
    final_location = loc_str

final_location