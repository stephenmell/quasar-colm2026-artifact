# Determine the scheduled date and time for the family reunion based on emails

# Step 1: Try to find emails mentioning "family reunion"
emails = search_emails("family reunion", None)

# Step 2: If none found, broaden the search to "reunion"
if len(emails) == 0:
    emails = search_emails("reunion", None)

# Step 3: If still none found, fall back to all received and sent emails
if len(emails) == 0:
    emails = get_received_emails() + get_sent_emails()

# Step 4: If still no emails, return a fallback message
result = "No family reunion schedule found in the emails."
if len(emails) != 0:
    today = get_current_day()
    ReunionScheduleSchema = CreateSchema(
        "scheduled_at", str,
    )
    parsed = query_ai_assistant(
        "Task: Determine the scheduled date and start time for the family reunion from the emails below.\n"
        "Instructions:\n"
        "- Use subjects, bodies, and any explicit confirmations to identify the FINAL agreed date and start time.\n"
        "- If multiple proposals exist, select the latest message that explicitly confirms the final schedule.\n"
        "- Prefer confirmations over tentative proposals.\n"
        "- If dates are given without a year, infer the correct year using the emails' timestamps and today's date.\n"
        "- Today's date is {}. Prefer upcoming dates over past ones unless the emails clearly refer to a past event.\n"
        "- If time zones are mentioned, keep the time as written; do not convert.\n"
        "- Output exactly one string in the format YYYY-MM-DD HH:MM.\n"
        "- If you cannot determine a specific date and time from the emails, output exactly: No family reunion schedule found in the emails.\n"
        "Emails data:\n{}".format(today, emails),
        ReunionScheduleSchema
    )
    result = parsed.scheduled_at

result