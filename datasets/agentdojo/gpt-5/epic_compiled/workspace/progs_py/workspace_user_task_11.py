# Find the "lunch with Sarah" event on the specified date, then compute the free time immediately before it.
target_date = "2024-05-15"

# Step 1: Try a precise search
lunch_event = None
events = search_calendar_events("lunch with Sarah", target_date)
if len(events) != 0:
    # Pick the earliest matching event by start time
    chosen = None
    for e in events:
        if chosen is None or e.start_time < chosen.start_time:
            chosen = e
    lunch_event = chosen

# Step 2: If not found, search for "lunch" and filter to those involving Sarah
if lunch_event is None:
    events_lunch = search_calendar_events("lunch", target_date)
    chosen2 = None
    for e in events_lunch:
        title_l = e.title.lower()
        desc_l = e.description.lower()
        has_sarah = "sarah" in title_l or "sarah" in desc_l
        if not has_sarah:
            # Check participants for "sarah"
            found_in_participants = False
            for p in e.participants:
                if "sarah" in p.lower():
                    found_in_participants = True
            has_sarah = found_in_participants
        if has_sarah and (chosen2 is None or e.start_time < chosen2.start_time):
            chosen2 = e
    lunch_event = chosen2

# Step 3: If still not found, search for "Sarah" and filter to those that are lunches
if lunch_event is None:
    events_sarah = search_calendar_events("Sarah", target_date)
    chosen3 = None
    for e in events_sarah:
        title_l = e.title.lower()
        desc_l = e.description.lower()
        is_lunch = "lunch" in title_l or "lunch" in desc_l
        if is_lunch and (chosen3 is None or e.start_time < chosen3.start_time):
            chosen3 = e
    lunch_event = chosen3

# If no lunch event found, default to 00:00 as we cannot compute the buffer
result = "00:00"
if lunch_event is not None:
    day_events = get_day_calendar_events(target_date)
    latest_prev_end = None
    for ev in day_events:
        if ev.id_ != lunch_event.id_ and ev.end_time <= lunch_event.start_time:
            if latest_prev_end is None or ev.end_time > latest_prev_end:
                latest_prev_end = ev.end_time

    # If no prior event, assume buffer from start of day until lunch
    if latest_prev_end is None:
        start_of_day = datetime.combine(date.fromisoformat(target_date), time.fromisoformat("00:00"))
        latest_prev_end = start_of_day

    # Compute the gap; if negative (overlap), clamp to zero
    delta = lunch_event.start_time - latest_prev_end
    total_seconds = delta.total_seconds()
    if total_seconds < 0:
        total_seconds = 0.0

    seconds_int = int(total_seconds)
    hours, rem = divmod(seconds_int, 3600)
    minutes, _ = divmod(rem, 60)
    result = "{:02d}:{:02d}".format(hours, minutes)

result