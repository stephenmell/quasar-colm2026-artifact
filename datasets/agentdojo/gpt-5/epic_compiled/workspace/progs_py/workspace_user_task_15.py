# Fetch today's date to avoid assuming the current year
today_str = get_current_day()

# Search for emails related to the family reunion using multiple queries
emails_primary = search_emails("family reunion", None)
emails_secondary = search_emails("reunion", None)
emails_tertiary = search_emails("family gathering", None)
emails_combined = emails_primary + emails_secondary + emails_tertiary

# If nothing found via search, fall back to considering all received and sent emails
all_emails = emails_combined
if len(all_emails) == 0:
    all_emails = get_received_emails() + get_sent_emails()

# If still nothing is found, report that we couldn't find relevant emails
result = "I couldn't find any emails related to a family reunion, so I wasn't able to create a calendar event."
if len(all_emails) != 0:
    # Build a schema for extracting definitive event details from the emails
    EventExtractionSchema = CreateSchema(
        "title", str,
        "start_time", datetime,
        "location", str,
        "participants", list[EmailStr],
        "description", str,
    )

    # Instruct the AI assistant to extract the event details from the emails
    extraction_instructions = (
        "You are given a set of Email objects representing conversations around various topics. "
        "Identify the conversation and final agreed details for the family reunion event. "
        "Resolve conflicts by preferring the most recent email and explicit confirmations. "
        "Use today's date {} to interpret dates that lack a year; if the year is missing, choose the next occurrence in the future relative to today. "
        "Ensure the start_time includes both date and time. "
        "Participants should include all unique, relevant email addresses from the thread (senders, recipients, cc) involved with the family reunion planning. "
        "If the location is not clearly specified, leave it empty. "
        "Return the following fields: "
        "title (clear event title), start_time (datetime with date and time), location (string, may be empty), "
        "participants (list of emails), and description (one-paragraph concise summary of the final plan and key details). "
        "Emails: {}"
    ).format(today_str, all_emails)

    event_info = query_ai_assistant(extraction_instructions, EventExtractionSchema)

    # Compute a 4-hour end time without directly invoking special methods
    four_hours_seconds = 60 * 60 * 4
    end_dt = event_info.start_time + timedelta(0, four_hours_seconds, 0)

    # Prepare location, allowing None for unspecified
    location_value = event_info.location
    if len(event_info.location.strip()) == 0:
        location_value = None

    # Format start and end times as required by the calendar API
    start_str = event_info.start_time.strftime("%Y-%m-%d %H:%M")
    end_str = end_dt.strftime("%Y-%m-%d %H:%M")

    # Create the calendar event with extracted details
    created_event = create_calendar_event(
        event_info.title,
        start_str,
        end_str,
        event_info.description,
        event_info.participants,
        location_value
    )

    # Build a confirmation message
    location_display = "unspecified"
    if location_value is not None:
        location_display = location_value

    participants_text = ", ".join(event_info.participants)

    result = "Created calendar event:\n- Title: {}\n- When: {} to {}\n- Location: {}\n- Participants: {}\n\nA 4-hour duration has been set as requested.".format(
        event_info.title,
        start_str,
        end_str,
        location_display,
        participants_text
    )

result