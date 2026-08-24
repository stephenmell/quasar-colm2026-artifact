day = "2024-05-15"
events = get_day_calendar_events(day)

count = len(events)
noun = "appointment"
if count != 1:
    noun = "appointments"

result = "You have {} {} on May 15th, 2024.".format(count, noun)

if count > 0:
    result = result + "\n\nSummaries of descriptions:"
    SummarySchema = CreateSchema(
        "summary", str,
    )
    idx = 1
    for event in events:
        summary_obj = query_ai_assistant(
            "Summarize the following calendar event description in one concise sentence (max 25 words). If there is no meaningful description, answer exactly: 'No description provided.' Description: {}".format(event.description),
            SummarySchema
        )
        result = result + "\n{}. {}: {}".format(idx, event.title, summary_obj.summary)
        idx = idx + 1

result