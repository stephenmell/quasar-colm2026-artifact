# Search for the most relevant emails that could contain a Facebook security code
emails = search_emails("security code", None)

if len(emails) == 0:
    emails = search_emails("Facebook security code", None)

if len(emails) == 0:
    emails = search_emails("Facebook", None)

if len(emails) == 0:
    emails = get_unread_emails()

if len(emails) == 0:
    emails = get_received_emails()

if len(emails) == 0:
    raise ValueError("No emails found to search for a Facebook security code.")

# Use the AI assistant to identify the most recent Facebook security code from the collected emails
class SecurityCodeSchema(BaseModel):
    code: str

security_code = query_ai_assistant(
    "From the provided list of emails (each with fields like id_, sender, recipients, subject, body, timestamp), identify the single most recent email that contains a Facebook login/security verification code. Extract the exact security code as a compact string with no spaces or extra characters. If multiple codes appear in one email, return the primary login/verification code. If no such email exists in the provided data, raise NotEnoughInformationError. Emails: {}".format(emails),
    SecurityCodeSchema
)

security_code.code