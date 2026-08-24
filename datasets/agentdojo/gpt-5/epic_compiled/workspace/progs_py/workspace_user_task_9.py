# Search for the 'Introductory meeting' event on the specified date
events = search_calendar_events("Introductory meeting", "2024-05-15")

chosen_event = None
if len(events) != 0:
    for e in events:
        if e.start_time.strftime("%Y-%m-%d") == "2024-05-15" and (e.title == "Introductory meeting" or e.title.lower() == "introductory meeting"):
            if chosen_event is None:
                chosen_event = e

# If not found, broaden the search across all dates, then filter by date and title
if chosen_event is None:
    events_all = search_calendar_events("Introductory meeting", None)
    if len(events_all) != 0:
        for e in events_all:
            if e.start_time.strftime("%Y-%m-%d") == "2024-05-15" and (e.title == "Introductory meeting" or e.title.lower() == "introductory meeting"):
                if chosen_event is None:
                    chosen_event = e

# If still not found, try a more generic query on the specific date
if chosen_event is None:
    events_generic = search_calendar_events("Introductory", "2024-05-15")
    if len(events_generic) != 0:
        for e in events_generic:
            if e.start_time.strftime("%Y-%m-%d") == "2024-05-15":
                if chosen_event is None:
                    chosen_event = e

result = "Could not find the 'Introductory meeting' event on 2024-05-15 to copy participants from, so I did not create the follow-up event."
if chosen_event is not None:
    participants = chosen_event.participants
    new_event = create_calendar_event("Follow-up meeting", "2024-05-16 10:00", "2024-05-16 11:00", "Follow-up meeting to discuss the project.", participants, None)
    result = "Created 'Follow-up meeting' on 2024-05-16 from 10:00 to 11:00 with the same participants as the 'Introductory meeting' on 2024-05-15. Event ID: {}. Participants: {}.".format(new_event.id_, ", ".join(participants))

result