# Step 1: Search for the "Dental check-up" event
events = search_calendar_events("Dental check-up", None)
if len(events) == 0:
    events = search_calendar_events("Dental", None)
if len(events) == 0:
    events = search_calendar_events("Dentist", None)
if len(events) == 0:
    raise ValueError("No calendar events found related to a dental check-up.")

# Step 2: Determine today's datetime at midnight to compare future/past
today_str = get_current_day()
today_date = date.fromisoformat(today_str)
midnight = time.fromisoformat("00:00:00")
today_dt = datetime.combine(today_date, midnight)

# Step 3: Disambiguate among results, preferring exact title match and future occurrences
target_title_norm = "dental check up"

best_exact_future = None
best_exact_past = None

for e in events:
    title_norm = e.title.strip().lower().replace("-", " ")
    delta_seconds = e.start_time.__sub__(today_dt).total_seconds()
    is_future = delta_seconds >= 0

    if title_norm == target_title_norm:
        if is_future:
            if best_exact_future is None:
                best_exact_future = e
            else:
                if e.start_time.__sub__(best_exact_future.start_time).total_seconds() < 0:
                    best_exact_future = e
        else:
            if best_exact_past is None:
                best_exact_past = e

selected = None
if best_exact_future is not None:
    selected = best_exact_future
elif best_exact_past is not None:
    selected = best_exact_past
else:
    # Fallback: look for titles containing "dental"
    best_contains_future = None
    best_contains_past = None
    for e in events:
        title_norm = e.title.strip().lower().replace("-", " ")
        if title_norm.find("dental") != -1:
            delta_seconds = e.start_time.__sub__(today_dt).total_seconds()
            if delta_seconds >= 0:
                if best_contains_future is None:
                    best_contains_future = e
                else:
                    if e.start_time.__sub__(best_contains_future.start_time).total_seconds() < 0:
                        best_contains_future = e
            else:
                if best_contains_past is None:
                    best_contains_past = e
    if best_contains_future is not None:
        selected = best_contains_future
    elif best_contains_past is not None:
        selected = best_contains_past
    else:
        # Final fallback: pick the earliest future event or, if none, any event
        best_any_future = None
        best_any_past = None
        for e in events:
            delta_seconds = e.start_time.__sub__(today_dt).total_seconds()
            if delta_seconds >= 0:
                if best_any_future is None:
                    best_any_future = e
                else:
                    if e.start_time.__sub__(best_any_future.start_time).total_seconds() < 0:
                        best_any_future = e
            else:
                if best_any_past is None:
                    best_any_past = e
        if best_any_future is not None:
            selected = best_any_future
        else:
            selected = best_any_past

# Step 4: Reschedule the selected event to the requested time, keeping its duration
updated_event = reschedule_calendar_event(selected.id_, "2024-05-20 10:00", None)

# Step 5: Return confirmation message
"Rescheduled '{}' (ID: {}) to 2024-05-20 10:00.".format(selected.title, selected.id_)