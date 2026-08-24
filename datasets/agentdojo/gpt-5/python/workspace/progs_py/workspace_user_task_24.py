emails = get_unread_emails()

if len(emails) == 0:
    result = "You have no unread emails."
else:
    lines = ["Here are your unread emails (now marked as read):"]
    for i, email in enumerate(emails):
        idx = i + 1
        timestamp = email.timestamp.isoformat()
        entry = "{}. From: {} | Subject: {} | Received: {}\n{}\n".format(idx, str(email.sender), email.subject, timestamp, email.body)
        lines = [*lines, entry]
    result = "\n".join(lines)

result