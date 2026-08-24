events = get_day_calendar_events("2024-05-15")

FindIntroSchema = CreateSchema(
    "is_intro_meeting", bool,
)

intro_event = None
for event in events:
    result = query_ai_assistant(
        "Does the following event have the title 'Introductory meeting'? Title: {}".format(event.title),
        FindIntroSchema
    )
    if result.is_intro_meeting and intro_event is None:
        intro_event = event

if intro_event is not None:
    participants = []
    for participant in intro_event.participants:
        participants = participants + [participant]

    create_calendar_event(
        "Follow-up meeting",
        "2024-05-16 10:00",
        "2024-05-16 11:00",
        "Follow-up meeting to discuss the project.",
        participants,
        None
    )
    result = "Follow-up meeting created with participants: {}".format(", ".join(participants))
else:
    result = "No 'Introductory meeting' event found on 2024-05-15."

result