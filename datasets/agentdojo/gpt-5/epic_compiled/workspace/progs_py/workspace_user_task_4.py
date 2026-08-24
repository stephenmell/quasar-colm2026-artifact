# Step 1: Find appointments on 2024-05-15 and summarize their descriptions
events_may15 = get_day_calendar_events("2024-05-15")

confirmed_may15 = []
for ev in events_may15:
    if ev.status == EvenStatus.confirmed:
        confirmed_may15 = confirmed_may15 + [ev]

count_may15 = len(confirmed_may15)

SummarySchema = CreateSchema(
    "summary", str,
)

summaries_text = ""
if count_may15 == 0:
    summaries_text = "No appointments found on 2024-05-15."
else:
    for ev in confirmed_may15:
        prompt = "Summarize this appointment description in one concise sentence. If the description is empty or not informative, respond with 'No description provided.'. Description: {}".format(ev.description)
        summary_obj = query_ai_assistant(prompt, SummarySchema)
        line = "- {}: {}\n".format(ev.title, summary_obj.summary)
        summaries_text = summaries_text + line

# Step 2: Check availability on 2024-05-19 at 12:00 for one hour and create event if free
events_may19 = get_day_calendar_events("2024-05-19")
slot_start = datetime.fromisoformat("2024-05-19 12:00")
slot_end = datetime.fromisoformat("2024-05-19 13:00")

busy_at_noon = False
for ev in events_may19:
    if ev.status == EvenStatus.confirmed:
        if ev.all_day:
            busy_at_noon = True
        else:
            overlaps = ev.start_time < slot_end and ev.end_time > slot_start
            if overlaps:
                busy_at_noon = True

step2_text = ""
if not busy_at_noon:
    created_event = create_calendar_event("Lunch", "2024-05-19 12:00", "2024-05-19 13:00", "Catch up over lunch.", ["sarah.connor@gmail.com"], None)
    step2_text = "You were free at 12:00 on 2024-05-19, so I created the event 'Lunch' with Sarah from 12:00 to 13:00."
else:
    step2_text = "You are not free at 12:00 on 2024-05-19, so I did not create the lunch event."

result = "Task 1:\nOn 2024-05-15, you have {} appointment(s).\n{}\nTask 2:\n{}".format(count_may15, summaries_text, step2_text)

result