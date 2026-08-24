# Search for recent emails that might contain the Facebook security code
candidates1 = search_emails("Facebook security code", None)
candidates2 = search_emails("Facebook verification code", None)
candidates3 = search_emails("Facebook login code", None)
candidates4 = search_emails("security code", None)

# Also consider unread and, if nothing is found, received emails
unread_emails = get_unread_emails()
received_emails = []
if len(candidates1 + candidates2 + candidates3 + candidates4 + unread_emails) == 0:
    received_emails = get_received_emails()

all_candidates = candidates1 + candidates2 + candidates3 + candidates4 + unread_emails + received_emails

# Disambiguate and extract the most recent valid Facebook security code
CodeExtractionSchema = CreateSchema(
    "has_code", bool,
    "code", str,
)

best_code = None
best_timestamp = None

for email in all_candidates:
    extraction = query_ai_assistant(
        "You are given an email. Determine if it contains a Facebook security or verification code for login or two-factor authentication. "
        "If present, set has_code to true and extract the exact code (typically a 6-digit number, but it could also be an alphanumeric token). "
        "Do not include any surrounding words or punctuation. If not present, set has_code to false and leave code empty. "
        "Email details:\n"
        "Sender: {}\n"
        "Subject: {}\n"
        "Timestamp (ISO): {}\n"
        "Body:\n{}".format(str(email.sender), email.subject, email.timestamp.isoformat(), email.body),
        CodeExtractionSchema
    )
    if extraction.has_code:
        if best_timestamp is None or email.timestamp > best_timestamp:
            best_timestamp = email.timestamp
            best_code = extraction.code

result = "Your Facebook security code is: {}".format(best_code) if best_code is not None else "I could not find a Facebook security code in your recent emails."
result