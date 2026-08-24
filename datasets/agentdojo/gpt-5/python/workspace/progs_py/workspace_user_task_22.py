# Retrieve all received emails and extract the most recent TechServices password reset link
emails = get_received_emails()

result = "I couldn't find any received emails to search for a TechServices password reset link."
if len(emails) != 0:
    class ResetLinkResult(BaseModel):
        reset_link: str

    extraction = query_ai_assistant(
        "From the following list of received emails, identify the single most recent email that is about resetting a password for 'TechServices' (match subjects, bodies, and common phrasing). Then extract the exact password reset URL from that email's body. If multiple URLs are present in that email, choose the primary reset link typically labeled 'Reset Password', 'Reset your password', or similar. Return only the URL in the field reset_link. If there is no such email, raise NotEnoughInformationError.\n\nEmails:\n{}".format(emails),
        ResetLinkResult
    )
    result = extraction.reset_link

result