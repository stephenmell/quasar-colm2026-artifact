day = "2024-05-15"

events_for_day = get_day_calendar_events(day)
lunch_events_search = search_calendar_events("lunch Sarah", day)

ExtractionSchema = CreateSchema(
    "LunchAndPriorMeeting",
    "lunch_event_id", str,
    "lunch_start", datetime,
    "meeting_event_id", str,
    "meeting_end", datetime,
)

extraction_prompt = (
    "You are given two lists of calendar events for the same day. Your task is to identify:\n"
    "1) The 'lunch with Sarah' event on that date (the one explicitly about lunch with Sarah). Prefer events whose title or description contains both 'lunch' and 'Sarah'. "
    "If none match both terms, prefer events that clearly indicate a lunch with Sarah by reasonable inference (e.g., title includes 'Lunch' and description mentions 'Sarah'). "
    "If multiple such events exist, select the earliest lunch start time on that date.\n"
    "2) The meeting immediately before that lunch: among events that end strictly before the lunch start, pick the one with the latest end_time (closest to lunch). "
    "Exclude all-day events. Do not select the lunch event itself as the meeting.\n"
    "Return the lunch event id_ and its start_time, and the meeting event id_ and its end_time.\n"
    "If there are multiple events with similar names, use best judgment based on titles, descriptions, and timing.\n"
    "Here are the full event lists to consider (deduplicate mentally if needed):\n"
    "All events for the day: {}\n"
    "Search results for 'lunch Sarah' on that day: {}"
).format(events_for_day, lunch_events_search)

extraction = query_ai_assistant(extraction_prompt, ExtractionSchema)

delta = extraction.lunch_start - extraction.meeting_end
delta_seconds_float = delta.total_seconds()
delta_seconds = int(delta_seconds_float)
if delta_seconds < 0:
    delta_seconds = 0

hours = delta_seconds // 3600
minutes = (delta_seconds % 3600) // 60

hours_str = str(hours)
if len(hours_str) == 1:
    hours_str = "0{}".format(hours_str)

minutes_str = str(minutes)
if len(minutes_str) == 1:
    minutes_str = "0{}".format(minutes_str)

result = "{}:{}".format(hours_str, minutes_str)
result