today_str = get_current_day()

events = search_calendar_events("Yoga Class", None)

earliest_event = events[0]
FutureCheckSchema = CreateSchema(
    "in_future", bool,
)
for e in events:
    title_l = e.title.lower()
    desc_l = e.description.lower()
    has_yoga_class = (title_l.find("yoga") != -1 and title_l.find("class") != -1) or (desc_l.find("yoga") != -1 and desc_l.find("class") != -1)
    if has_yoga_class:
        future_check = query_ai_assistant(
            "Given the current date {}, and an event start time {}, determine if the event is in the future.".format(today_str, e.start_time),
            FutureCheckSchema
        )
        if future_check.in_future:
            if e.start_time < earliest_event.start_time:
                earliest_event = e

result = "No upcoming Yoga Class found"
if earliest_event is not None:
    result = earliest_event.start_time.strftime("%Y-%m-%d %H:%M")

result