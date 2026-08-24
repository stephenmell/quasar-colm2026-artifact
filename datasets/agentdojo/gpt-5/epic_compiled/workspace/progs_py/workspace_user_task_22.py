# Regenerate corrected code to find the most recent TechServices password reset link without referencing undefined variables.

# Step 1: Search for relevant emails with progressively broader queries
emails = search_emails("TechServices password reset", None)

if len(emails) == 0:
    emails = search_emails("TechServices", None)

if len(emails) == 0:
    emails = search_emails("password reset", None)

if len(emails) == 0:
    emails = search_emails("", None)

# Step 2: Define schema to extract the reset link from candidate emails
ResetLinkSchema = CreateSchema(
    "reset_link", str,
)

# Step 3: Iterate through emails to find the most recent valid TechServices reset link
best_link = ""
best_timestamp = None

for email in emails:
    extraction = query_ai_assistant(
        "From this email, extract the single URL that is the password reset link for the service named 'TechServices'. "
        "If this is not a TechServices password reset email or there is no reset link, return an empty string in reset_link. "
        "Choose the link explicitly intended to reset the password, not links to help centers or general login pages. "
        "Email Subject: {}. Email Body: {}".format(email.subject, email.body),
        ResetLinkSchema
    )
    link = extraction.reset_link
    if link != "":
        if best_link == "":
            best_link = link
            best_timestamp = email.timestamp
        else:
            if email.timestamp > best_timestamp:
                best_link = link
                best_timestamp = email.timestamp

# Step 4: Prepare the final result
result = "Here is your TechServices password reset link: {}".format(best_link) if best_link != "" else "I could not find a TechServices password reset link in your recent emails."

result