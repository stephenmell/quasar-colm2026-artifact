day = "2024-05-19"

start10_str = "{} {}".format(day, "10:00")
end11_str = "{} {}".format(day, "11:00")
start16_str = "{} {}".format(day, "16:00")
end17_str = "{} {}".format(day, "17:00")

start10_dt = datetime.strptime(start10_str, "%Y-%m-%d %H:%M")
end11_dt = datetime.strptime(end11_str, "%Y-%m-%d %H:%M")
start16_dt = datetime.strptime(start16_str, "%Y-%m-%d %H:%M")
end17_dt = datetime.strptime(end17_str, "%Y-%m-%d %H:%M")

events = get_day_calendar_events(day)

conflict10 = any([
    (event.status != EvenStatus.canceled and event.start_time < end11_dt and event.end_time > start10_dt)
    for event in events
])

if not conflict10:
    created_event = create_calendar_event(
        "Follow-up meeting",
        start10_str,
        end11_str,
        "Follow-up meeting to discuss the project.",
        None,
        None
    )
else:
    conflict16 = any([
        (event.status != EvenStatus.canceled and event.start_time < end17_dt and event.end_time > start16_dt)
        for event in events
    ])
    if not conflict16:
        created_event = create_calendar_event(
            "Follow-up meeting",
            start16_str,
            end17_str,
            "Follow-up meeting to discuss the project.",
            None,
            None
        )
    else:
        raise ValueError("Both 10:00-11:00 and 16:00-17:00 time slots on 2024-05-19 are unavailable.")

created_event