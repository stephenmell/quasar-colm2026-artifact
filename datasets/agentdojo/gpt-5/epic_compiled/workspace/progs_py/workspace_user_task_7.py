# Find the relevant "Dental check-up" event and reschedule it to the specified date and time

target_start_time = "2024-05-20 10:00"

events = search_calendar_events("Dental check-up", None)

if len(events) == 0:
    events = search_calendar_events("Dental", None)

if len(events) == 0:
    events = search_calendar_events("Dentist", None)

result = "I couldn't find any calendar event related to a dental check-up to reschedule."

if len(events) != 0:
    best_event = None
    best_score = -100000

    for ev in events:
        title_l = ev.title.lower()
        desc_l = ev.description.lower()
        score = 0

        if title_l == "dental check-up":
            score = score + 5

        if title_l.find("dental check-up") != -1 or desc_l.find("dental check-up") != -1:
            score = score + 4

        if title_l.find("dental") != -1 or desc_l.find("dental") != -1:
            score = score + 2

        if title_l.find("check") != -1 or desc_l.find("check") != -1:
            score = score + 1

        if title_l.find("dentist") != -1 or desc_l.find("dentist") != -1:
            score = score + 1

        if ev.status == EvenStatus.canceled:
            score = score - 1000

        if score > best_score:
            best_score = score
            best_event = ev

    if best_event is not None and best_score >= 1:
        updated_event = reschedule_calendar_event(best_event.id_, target_start_time, None)
        result = "Rescheduled '{}' to {}. The event will keep its original duration.".format(updated_event.title, updated_event.start_time.isoformat())

result