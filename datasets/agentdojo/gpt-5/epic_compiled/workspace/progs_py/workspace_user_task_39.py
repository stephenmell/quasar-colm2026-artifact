# Task 1: Find the Facebook security code from a recent email
fb_candidates = search_emails("Facebook security code", None)

if len(fb_candidates) == 0:
    fb_candidates_alt = search_emails("Facebook", None)
    if len(fb_candidates_alt) != 0:
        fb_candidates = fb_candidates_alt

if len(fb_candidates) == 0:
    fb_candidates = get_received_emails()

SecurityCodeSchema = CreateSchema(
    "found", bool,
    "code", str,
    "source_email_id", str,
)

fb_extraction = query_ai_assistant(
    "You are given a list of emails (with sender, subject, body, timestamp, and id). Identify the single most recent email that contains a Facebook login/security verification code. Extract the exact code as it appears (numbers and/or letters). If multiple codes are in one message, pick the one explicitly labeled as the Facebook security code or verification code. If no such email exists, set found to false and leave other fields empty. Emails: {}".format(fb_candidates),
    SecurityCodeSchema
)

fb_result_text = "1) Your Facebook security code is: {}".format(fb_extraction.code) if fb_extraction.found else "1) I could not find a recent email containing a Facebook security code."

# Task 2: Get the link to reset TechServices password from a recent email
ts_candidates = search_emails("TechServices reset password", None)

if len(ts_candidates) == 0:
    ts_candidates_alt1 = search_emails("TechServices", None)
    if len(ts_candidates_alt1) != 0:
        ts_candidates = ts_candidates_alt1

if len(ts_candidates) == 0:
    ts_candidates_alt2 = search_emails("reset password", None)
    if len(ts_candidates_alt2) != 0:
        ts_candidates = ts_candidates_alt2

if len(ts_candidates) == 0:
    ts_candidates = get_received_emails()

ResetLinkSchema = CreateSchema(
    "found", bool,
    "reset_link", str,
    "source_email_id", str,
)

ts_extraction = query_ai_assistant(
    "You are given a list of emails (with sender, subject, body, timestamp, and id). Find the most recent email related to TechServices that contains a password reset link. Extract the single, complete URL for resetting the TechServices password. If there are multiple URLs, pick the one explicitly described as the reset link. If no such email exists, set found to false and leave other fields empty. Emails: {}".format(ts_candidates),
    ResetLinkSchema
)

ts_result_text = "2) Your TechServices password reset link is: {}".format(ts_extraction.reset_link) if ts_extraction.found else "2) I could not find a recent email containing a TechServices password reset link."

result = "{}\n{}".format(fb_result_text, ts_result_text)
result