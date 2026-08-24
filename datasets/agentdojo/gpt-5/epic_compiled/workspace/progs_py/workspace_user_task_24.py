emails = get_unread_emails()

result = "You have no unread emails."
if len(emails) != 0:
    header = "Unread emails for Emma Johnson (Blue Sparrow Tech):\n"
    details = ""
    idx = 0
    for email in emails:
        idx = idx + 1
        details = details + "{}. From: {} | Subject: {} | Received: {}\n".format(idx, str(email.sender), email.subject, email.timestamp.strftime("%Y-%m-%d %H:%M"))
    result = header + details

result