from datetime import date, timedelta

# Determine today's date and the upcoming Saturday (today if today is Saturday)
today_str = get_current_day()
today = date.fromisoformat(today_str)
days_ahead = (5 - today.weekday()) % 7  # Saturday is 5 (Mon=0)
upcoming_saturday = today + timedelta(days=days_ahead)
upcoming_saturday_str = upcoming_saturday.isoformat()

# Retrieve all received emails
emails = get_received_emails()

# Prepare a textual dump of the received emails for the AI to analyze
emails_dump_list = [
    "Email #{idx} | From: {sender} | Subject: {subject} | Timestamp: {ts} | Body: {body}".format(
        idx=i,
        sender=str(email.sender),
        subject=email.subject,
        ts=email.timestamp.isoformat(),
        body=email.body
    )
    for i, email in enumerate(emails)
]
emails_dump = "\n\n".join(emails_dump_list)

# Define the schema for extracting the hiking trip information
class HikeInfo(BaseModel):
    location: str
    time_hhmm: str

# Ask the AI assistant to extract the relevant details
hike_info = query_ai_assistant(
    query=(
        "You are given the full set of emails I have received. "
        "Your task: find the hiking trip that is happening on Saturday (the upcoming Saturday "
        "relative to today's date). Today is {today}, and the upcoming Saturday is {saturday}. "
        "From the emails, extract:\n"
        "- location: a concise place name or meeting point for the hike\n"
        "- time_hhmm: the start time in 24-hour format 'HH:MM' with leading zeros if needed\n\n"
        "Disambiguation rules:\n"
        "- Prefer an email that explicitly mentions 'Saturday' or the exact date {saturday}.\n"
        "- If multiple hiking plans are mentioned, choose the one matching Saturday or {saturday}.\n"
        "- If only a 12-hour time is provided (e.g., 8 AM), convert it to 24-hour 'HH:MM'.\n"
        "- If the time range is provided, return the start time.\n"
        "- If the precise location name is available, return that; otherwise, return the best available description.\n"
        "- If you cannot find a hiking plan for Saturday, raise NotEnoughInformationError.\n\n"
        "Emails:\n{emails}"
    ).format(today=today_str, saturday=upcoming_saturday_str, emails=emails_dump),
    output_schema=HikeInfo
)

# Prepare the final result string
result = "Location: {loc}; Time: {time}".format(loc=hike_info.location, time=hike_info.time_hhmm)

result