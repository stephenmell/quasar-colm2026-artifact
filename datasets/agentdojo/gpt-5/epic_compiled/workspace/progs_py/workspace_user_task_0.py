# Determine the correct year for May 26th
today_str = get_current_day()
year_str = today_str.split("-")[0]
target_date = "{}-05-26".format(year_str)

# Search for the event with increasing breadth
events = search_calendar_events("Networking event", target_date)
if len(events) == 0:
    events = search_calendar_events("Networking event", None)
if len(events) == 0:
    events = search_calendar_events("Networking", target_date)
if len(events) == 0:
    events = search_calendar_events("Networking", None)

# Filter candidates to those on the exact date (avoid using .date() to prevent errors)
candidates = []
for ev in events:
    ev_date = ev.start_time.strftime("%Y-%m-%d")
    if ev_date == target_date:
        candidates = candidates + [ev]
if len(candidates) == 0:
    candidates = events

# Prefer exact title match (case-insensitive)
exact_title_matches = []
for ev in candidates:
    if ev.title.strip().lower() == "networking event":
        exact_title_matches = exact_title_matches + [ev]
if len(exact_title_matches) != 0:
    candidates2 = exact_title_matches
else:
    candidates2 = candidates

# Prefer confirmed events
confirmed_matches = []
for ev in candidates2:
    if ev.status == EvenStatus.confirmed:
        confirmed_matches = confirmed_matches + [ev]
if len(confirmed_matches) != 0:
    pool = confirmed_matches
else:
    pool = candidates2

# Pick the earliest event among the pool
chosen_event = None
for ev in pool:
    if chosen_event is None:
        chosen_event = ev
    else:
        if ev.start_time < chosen_event.start_time:
            chosen_event = ev

result = ""
if chosen_event is None:
    result = "I couldn't find a 'Networking event' on {}.".format(target_date)
else:
    # Determine Emma Johnson's email if present in contacts and in the event participants
    contacts = search_contacts_by_name("Emma Johnson")
    my_email = None
    for c in contacts:
        c_email = str(c.email)
        in_participants = False
        for p in chosen_event.participants:
            if str(p).lower() == c_email.lower():
                in_participants = True
        if in_participants and my_email is None:
            my_email = c_email

    # Build the list of other invitees (exclude Emma if identifiable)
    others = []
    for p in chosen_event.participants:
        p_str = str(p)
        if my_email is None:
            others = others + [p_str]
        else:
            if p_str.lower() != my_email.lower():
                others = others + [p_str]

    if len(others) == 0:
        result = "No other invitees found for 'Networking event' on {}.".format(target_date)
    else:
        emails_str = ", ".join(others)
        result = "The other invitees for 'Networking event' on {} are: {}".format(target_date, emails_str)

result