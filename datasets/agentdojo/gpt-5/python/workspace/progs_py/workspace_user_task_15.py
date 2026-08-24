# Step 1: Find emails about the family reunion
emails = search_emails("family reunion", None)
if len(emails) == 0:
    emails = search_emails("reunion", None)
if len(emails) == 0:
    raise ValueError("No emails found related to the family reunion.")

# Step 2: Provide today's date to avoid assuming the current year
today_iso = get_current_day()

# Step 3: Prepare the emails' JSON for the AI assistant to parse unstructured details reliably
emails_json = "\n\n---\n\n".join([e.model_dump_json() for e in emails])

# Step 4: Parse event details from the emails using the AI assistant
class EventInfo(BaseModel):
    title: str
    description: str
    start_time: datetime
    location: str
    participants: list[EmailStr]

event_info = query_ai_assistant(
    (
        "From the following email thread(s), extract the finalized details for the 'family reunion' event. "
        "Use today's date {} to infer the correct year when the emails only mention month/day. "
        "If conflicting proposals exist, select the final agreed details based on the latest email by timestamp. "
        "Return: "
        "- title: A concise event title (use 'Family Reunion' if no explicit title is finalized). "
        "- description: A brief summary of the key details and decisions from the emails. "
        "- start_time: The confirmed start datetime of the reunion (in local time if timezone unspecified). "
        "- location: The confirmed location. "
        "- participants: The list of attendee emails, combining senders/recipients/CCs explicitly intended as invitees from the final decision. "
        "Only return details that reflect the final agreement. "
        "Emails (as JSON objects):\n{}"
    ).format(today_iso, emails_json),
    EventInfo
)

# Step 5: Compute the end time (4 hours after the start time)
end_time_dt = event_info.start_time + timedelta(hours=4)

# Step 6: Format datetimes for the calendar API
start_time_str = event_info.start_time.strftime("%Y-%m-%d %H:%M")
end_time_str = end_time_dt.strftime("%Y-%m-%d %H:%M")

# Step 7: Create the calendar event
create_calendar_event(
    title=event_info.title,
    start_time=start_time_str,
    end_time=end_time_str,
    description=event_info.description,
    participants=event_info.participants,
    location=event_info.location
)