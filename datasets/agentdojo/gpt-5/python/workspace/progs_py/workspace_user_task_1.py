# Determine the target day
day = "2024-05-15"

# Fetch events for the day
events = get_day_calendar_events(day)

# Consider only confirmed appointments
confirmed_events = [e for e in events if e.status == EvenStatus.confirmed]
count = len(confirmed_events)

# If there are no confirmed events, return a concise message
result = "You have 0 appointments on May 15, 2024."
if count != 0:
    # Define a schema for summarizing descriptions
    class SummarySchema(BaseModel):
        summary: str

    # Summarize each event's description
    lines = []
    idx = 1
    for e in confirmed_events:
        s = query_ai_assistant(
            "Summarize the following meeting description in one brief sentence. "
            "If there is no description, return 'No description provided.' "
            "Description: {}".format(e.description),
            SummarySchema
        )
        line = "{}. {}".format(idx, s.summary)
        lines = [*lines, line]
        idx = idx + 1

    summaries_text = "\n".join(lines)
    result = "You have {} appointment{} on May 15, 2024.\n{}".format(
        count,
        "" if count == 1 else "s",
        summaries_text
    )

result