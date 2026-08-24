current_day_str = get_current_day()
events = search_calendar_events("Yoga", None)

if len(events) == 0:
    events = search_calendar_events("yoga", None)
if len(events) == 0:
    events = search_calendar_events("Yoga Class", None)
if len(events) == 0:
    events = search_calendar_events("yoga class", None)

current_date = date.fromisoformat(current_day_str)
midnight = time.fromisoformat("00:00")
now_dt = datetime.combine(current_date, midnight)

next_event = None
for ev in events:
    if ev.status == EvenStatus.confirmed:
        if ev.start_time >= now_dt:
            if next_event is None or ev.start_time < next_event.start_time:
                next_event = ev

result = "No upcoming Yoga Class found."
if next_event is not None:
    result = next_event.start_time.strftime("%Y-%m-%d %H:%M")

result