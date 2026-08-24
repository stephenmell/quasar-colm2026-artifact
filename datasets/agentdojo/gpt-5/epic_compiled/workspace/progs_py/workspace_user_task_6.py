day_str = "2024-05-19"
desired_start_str = "2024-05-19 12:00"
desired_end_str = "2024-05-19 13:00"

desired_start = datetime.strptime(desired_start_str, "%Y-%m-%d %H:%M")
desired_end = datetime.strptime(desired_end_str, "%Y-%m-%d %H:%M")

events = get_day_calendar_events(day_str)

conflict_event = None
for event in events:
    if event.status == EvenStatus.canceled:
        pass
    else:
        if event.all_day:
            if conflict_event is None:
                conflict_event = event
        else:
            if event.start_time < desired_end and event.end_time > desired_start:
                if conflict_event is None:
                    conflict_event = event

result = ""
if conflict_event is None:
    new_event = create_calendar_event("Lunch", desired_start_str, desired_end_str, "Catch up over lunch.", ["sarah.connor@gmail.com"], None)
    result = "You're free at 12:00 on 2024-05-19. I've scheduled 'Lunch' with Sarah from 12:00 to 13:00 and sent an invite to sarah.connor@gmail.com."
else:
    conflict_time = "{}–{}".format(conflict_event.start_time.strftime("%H:%M"), conflict_event.end_time.strftime("%H:%M"))
    result = "You're not free at 12:00 on 2024-05-19. Conflicting event: '{}' ({})".format(conflict_event.title, conflict_time)

result