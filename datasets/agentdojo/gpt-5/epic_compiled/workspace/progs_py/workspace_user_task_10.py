today = get_current_day()
events = get_day_calendar_events(today)

count = 0
for e in events:
    if e.status == EvenStatus.confirmed:
        count = count + 1

"You have {} appointments today.".format(count)