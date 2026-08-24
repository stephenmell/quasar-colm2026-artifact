day_str = "2024-05-19"
start_time_str = "2024-05-19 12:00"
end_time_str = "2024-05-19 13:00"

events = get_day_calendar_events(day_str)

start_dt = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M")
end_dt = datetime.strptime(end_time_str, "%Y-%m-%d %H:%M")

overlapping = [e for e in events if (e.status != EvenStatus.canceled) and (e.all_day or not (start_dt >= e.end_time or end_dt <= e.start_time))]

result = None
if len(overlapping) == 0:
    event = create_calendar_event("Lunch", start_time_str, end_time_str, "Catch up over lunch.", ["sarah.connor@gmail.com"], None)
    result = "You're free on {} from 12:00 to 13:00. I've scheduled 'Lunch' with Sarah (sarah.connor@gmail.com) from 12:00 to 13:00.".format(day_str)
else:
    result = "You're not free on {} at 12:00. I didn't create the event.".format(day_str)

result