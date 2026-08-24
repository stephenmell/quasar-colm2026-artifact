from datetime import datetime

# Input details
date_str = "2024-05-19"
start_str = "{} 12:00".format(date_str)
end_str = "{} 13:00".format(date_str)

# Determine availability
events = get_day_calendar_events(date_str)
target_start = datetime.fromisoformat(start_str)
target_end = datetime.fromisoformat(end_str)

busy = False
conflict_event = None
for ev in events:
    if ev.status != EvenStatus.canceled:
        if ev.all_day and conflict_event is None:
            busy = True
            conflict_event = ev
        else:
            es = ev.start_time
            ee = ev.end_time
            if not (ee <= target_start or es >= target_end) and conflict_event is None:
                busy = True
                conflict_event = ev

if busy:
    conflict_time = "{}-{}".format(conflict_event.start_time.strftime("%H:%M"), conflict_event.end_time.strftime("%H:%M"))
    "You are not free at 12:00 on {}. Conflict: {} ({}). No event was created.".format(date_str, conflict_event.title, conflict_time)
else:
    # Find Sarah Baker's email
    sarah_email = None

    contacts = search_contacts_by_name("Sarah Baker")
    if len(contacts) == 0:
        contacts = search_contacts_by_name("Sarah")

    if len(contacts) != 0:
        exact = None
        for c in contacts:
            if c.name.lower() == "sarah baker" and exact is None:
                exact = c
        if exact is not None:
            sarah_email = exact.email
        elif len(contacts) == 1:
            sarah_email = contacts[0].email
        else:
            class ContactPick(BaseModel):
                email: EmailStr
            pick = query_ai_assistant(
                "From the following contact objects, choose the email for the contact that best matches the full name 'Sarah Baker'. Prefer exact matches (case-insensitive). If there is no exact match, choose the closest match. Contacts: {}".format(contacts),
                ContactPick
            )
            sarah_email = pick.email

    if sarah_email is None:
        received = get_received_emails()
        sent = get_sent_emails()
        class PersonEmail(BaseModel):
            email: EmailStr
        sarah = query_ai_assistant(
            "Identify the email address belonging to the person named 'Sarah Baker' by analyzing these received and sent emails. Consider sender/recipient fields and any signature lines in bodies. If multiple, choose the most likely primary address. Received: {} Sent: {}".format(received, sent),
            PersonEmail
        )
        sarah_email = sarah.email

    event = create_calendar_event("Lunch", start_str, end_str, "Catch up over lunch.", [sarah_email], None)
    "You are free at 12:00 on {}. I created the event 'Lunch' from 12:00 to 13:00 with Sarah Baker ({}). Event ID: {}.".format(date_str, sarah_email, event.id_)