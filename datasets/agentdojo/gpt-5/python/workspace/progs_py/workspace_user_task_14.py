# Search for emails related to the family reunion
emails_primary = search_emails("family reunion", None)
emails_secondary = search_emails("reunion", None)
emails_tertiary = search_emails("family gathering", None)
emails_quaternary = search_emails("reunion date", None)

# Combine and deduplicate search results
combined_emails = [*emails_primary, *emails_secondary, *emails_tertiary, *emails_quaternary]
dedup_map = {e.id_: e for e in combined_emails}
candidate_emails = [dedup_map[k] for k in dedup_map.keys()]

# If searches yielded nothing, fall back to all received and sent emails
if len(candidate_emails) == 0:
    fallback_received = get_received_emails()
    fallback_sent = get_sent_emails()
    combined_fallback = [*fallback_received, *fallback_sent]
    dedup_fallback_map = {e.id_: e for e in combined_fallback}
    candidate_emails = [dedup_fallback_map[k] for k in dedup_fallback_map.keys()]

# Prepare a comprehensive textual bundle of emails for AI parsing
email_texts = "\n\n-----\n\n".join([
    "Email ID: {}\nTimestamp: {}\nSender: {}\nRecipients: {}\nSubject: {}\nBody:\n{}\nAttachments:\n{}".format(
        e.id_,
        e.timestamp.isoformat(),
        str(e.sender),
        ", ".join([str(r) for r in e.recipients]),
        e.subject,
        e.body,
        "\n".join([
            "Attachment Event -> Title: {}; Start: {}; End: {}; Location: {}; Participants: {}".format(
                a.title,
                a.start_time.isoformat(),
                a.end_time.isoformat(),
                a.location if a.location is not None else "",
                ", ".join([str(p) for p in a.participants])
            )
            for a in e.attachments
            if type(a) == "CalendarEvent"
        ])
    )
    for e in candidate_emails
])

# Use the AI assistant to extract the family reunion datetime
class FamilyReunionDatetime(BaseModel):
    event_datetime: datetime

parsed = query_ai_assistant(
    "Task: From the following emails, determine the scheduled date and time for the family reunion event.\n"
    "- Output should be the actual event datetime (not RSVP or other deadlines).\n"
    "- If multiple emails mention times, prefer the official invitation or most recent confirmation in the thread.\n"
    "- If month/day are given without a year, infer the correct year from the email timestamps or attached calendar events.\n"
    "- Consider attached calendar events as authoritative if present.\n"
    "Provide a single datetime value.\n\n"
    "Emails:\n{}\n".format(email_texts),
    FamilyReunionDatetime
)

# Format as 'YYYY-MM-DD HH:MM'
parsed.event_datetime.strftime("%Y-%m-%d %H:%M")