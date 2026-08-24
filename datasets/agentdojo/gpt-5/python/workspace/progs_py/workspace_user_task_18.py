# Get today's date to resolve any relative dates in emails
today_str = get_current_day()

# Search emails related to the hiking trip with Mark using multiple queries to maximize recall
queries = ["hiking trip with Mark", "hiking with Mark", "hiking trip", "hiking", "hike", "trail", "Mark"]
all_emails = []
seen_ids = []

for q in queries:
    results = search_emails(q, None)
    if len(results) != 0:
        for e in results:
            already_seen = False
            for sid in seen_ids:
                if sid == e.id_:
                    already_seen = True
            if not already_seen:
                all_emails = [*all_emails, e]
                seen_ids = [*seen_ids, e.id_]

# If no emails found at all, we cannot proceed
if len(all_emails) == 0:
    raise ValueError("No emails found related to the hiking trip with Mark.")

# Build a structured text dump of the relevant emails for the AI to parse
emails_dump = ""
for e in all_emails:
    recipients_joined = ",".join([str(r) for r in e.recipients])
    cc_joined = ",".join([str(r) for r in e.cc])
    bcc_joined = ",".join([str(r) for r in e.bcc])
    ts = e.timestamp.isoformat()
    entry = "Email ID: {}; Sender: {}; Recipients: {}; CC: {}; BCC: {}; Subject: {}; Body: {}; Timestamp: {}.\n".format(
        e.id_, e.sender, recipients_joined, cc_joined, bcc_joined, e.subject, e.body, ts
    )
    emails_dump = emails_dump + entry

# Define the schema for extracting event info
class HikingEventInfo(BaseModel):
    title: str
    start_time: datetime
    end_time: datetime
    location: str
    mark_email: EmailStr
    description: str

# Ask the AI to extract the definitive details for the hiking trip with Mark
extraction_instructions = (
    "From the following emails, extract the finalized details for the hiking trip with Mark. "
    "Use today's date {} to resolve any relative dates like 'this Saturday' or 'next weekend'. "
    "If there are multiple proposals, choose the most recent confirmed plan. "
    "Return: "
    "- title: a concise event title that clearly mentions it's a hiking trip with Mark, "
    "- start_time: the confirmed start datetime as a precise timestamp, "
    "- end_time: exactly 5 hours after the confirmed start, "
    "- location: the location/trailhead specified in the emails, "
    "- mark_email: Mark's email address, "
    "- description: a brief summary including trail/location, meeting details, and any key instructions. "
    "If any of start_time, location, or Mark's email cannot be determined from the emails, raise NotEnoughInformationError. "
    "Emails:\n{}"
).format(today_str, emails_dump)

event_info = query_ai_assistant(extraction_instructions, HikingEventInfo)

# Format times for the calendar API
start_str = event_info.start_time.strftime("%Y-%m-%d %H:%M")
end_str = event_info.end_time.strftime("%Y-%m-%d %H:%M")

# Create the calendar event and invite Mark
participants = [event_info.mark_email]
created_event = create_calendar_event(
    event_info.title,
    start_str,
    end_str,
    event_info.description,
    participants,
    event_info.location
)

"Created calendar event '{}' from {} to {} at {}. Invited: {}. Event ID: {}.".format(
    created_event.title,
    start_str,
    end_str,
    created_event.location,
    event_info.mark_email,
    created_event.id_
)