day = get_current_day()
events = get_day_calendar_events(day)
confirmed_events = [e for e in events if e.status == EvenStatus.confirmed]
len(confirmed_events)