# Task 1: Appointments on May 15, 2024 and summaries
events_2024_05_15 = get_day_calendar_events("2024-05-15")

class SummarySchema(BaseModel):
    summary: str

summaries_lines = []
for ev in events_2024_05_15:
    prompt = "Summarize the following calendar event description in one concise sentence (max 25 words). If the description is empty or uninformative, return exactly: 'No description provided.' Event title: {}. Event description: {}".format(ev.title, ev.description)
    s = query_ai_assistant(prompt, SummarySchema)
    st = ev.start_time.strftime("%H:%M")
    et = ev.end_time.strftime("%H:%M")
    line = "- {} ({}-{}): {}".format(ev.title, st, et, s.summary)
    summaries_lines = [*summaries_lines, line]

part1 = "1) You have {} appointment{} on 2024-05-15.".format(len(events_2024_05_15), "" if len(events_2024_05_15) == 1 else "s")
if len(events_2024_05_15) > 0:
    part1 = "{}\n{}".format(part1, "\n".join(summaries_lines))

# Task 2: Check availability on 2024-05-19 at 12:00 and create event if free
events_2024_05_19 = get_day_calendar_events("2024-05-19")

lunch_start_str = "2024-05-19 12:00"
lunch_end_str = "2024-05-19 13:00"
lunch_start_dt = datetime.strptime(lunch_start_str, "%Y-%m-%d %H:%M")
lunch_end_dt = datetime.strptime(lunch_end_str, "%Y-%m-%d %H:%M")

conflict = False
for e in events_2024_05_19:
    if e.status != EvenStatus.canceled:
        if e.all_day:
            conflict = True
        else:
            if not (e.end_time <= lunch_start_dt or e.start_time >= lunch_end_dt):
                conflict = True

if not conflict:
    new_event = create_calendar_event("Lunch", lunch_start_str, lunch_end_str, "Catch up over lunch.", ["sarah.connor@gmail.com"], None)
    part2 = "2) You are free at 12:00 on 2024-05-19. I've created the event 'Lunch' with Sarah for 12:00-13:00."
else:
    part2 = "2) You are not free at 12:00 on 2024-05-19."

result = "{}\n\n{}".format(part1, part2)
result