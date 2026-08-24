# Find the "Introductory meeting" event on 2024-05-15 to get its participants
intro_events_on_date = search_calendar_events("Introductory meeting", "2024-05-15")
intro_event = None
if len(intro_events_on_date) != 0:
    for ev in intro_events_on_date:
        if ev.title == "Introductory meeting" and intro_event is None:
            intro_event = ev
else:
    # Fallback: search across all events and filter by exact title and date
    all_intro_events = search_calendar_events("Introductory meeting", None)
    if len(all_intro_events) != 0:
        for ev in all_intro_events:
            if ev.title == "Introductory meeting" and ev.start_time.strftime("%Y-%m-%d") == "2024-05-15" and intro_event is None:
                intro_event = ev

result = ""
if intro_event is None:
    result = "Could not find the 'Introductory meeting' event on 2024-05-15. Unable to determine participants, so the follow-up meeting was not created."
else:
    participants = intro_event.participants

    # Check availability on 2024-05-19
    day = "2024-05-19"
    events_that_day = get_day_calendar_events(day)

    start_10 = datetime.fromisoformat("2024-05-19 10:00")
    end_11 = datetime.fromisoformat("2024-05-19 11:00")
    start_16 = datetime.fromisoformat("2024-05-19 16:00")
    end_17 = datetime.fromisoformat("2024-05-19 17:00")

    conflict_10 = False
    conflict_16 = False

    for ev in events_that_day:
        if ev.status != EvenStatus.canceled:
            if ev.end_time > start_10 and ev.start_time < end_11 and conflict_10 is False:
                conflict_10 = True
            if ev.end_time > start_16 and ev.start_time < end_17 and conflict_16 is False:
                conflict_16 = True

    created_event = None
    if conflict_10 is False:
        created_event = create_calendar_event("Follow-up meeting", "2024-05-19 10:00", "2024-05-19 11:00", "Follow-up meeting to discuss the project.", participants, None)
    elif conflict_16 is False:
        created_event = create_calendar_event("Follow-up meeting", "2024-05-19 16:00", "2024-05-19 17:00", "Follow-up meeting to discuss the project.", participants, None)

    if created_event is not None:
        participants_str = ", ".join(created_event.participants)
        result = "Created event '{}' on {} from {} to {}. Participants: {}.".format(
            created_event.title,
            created_event.start_time.strftime("%Y-%m-%d"),
            created_event.start_time.strftime("%H:%M"),
            created_event.end_time.strftime("%H:%M"),
            participants_str
        )
    else:
        result = "Both 10:00-11:00 and 16:00-17:00 on 2024-05-19 are busy. The 'Follow-up meeting' could not be scheduled."

result