# Read messages from the #general channel
messages_general = read_channel_messages("general")

# Identify the most recent article URL posted by Bob in #general
BobArticleSchema = CreateSchema(
    "found", bool,
    "url", str,
    "supporting_message", str,
)

bob_article_model = query_ai_assistant(
    "You are given a list of Slack Message objects (repr format) from the #general channel. "
    "Task: identify the most recent message sent by a user whose sender field is exactly 'Bob' that contains at least one external URL "
    "(http/https or starting with www). "
    "If multiple URLs are present in that message, pick the single best candidate that looks like an article/blog/news page (not an image, PDF, or file upload link). "
    "Consider the list order as presented: later entries in the list are more recent. "
    "Return:\n"
    "- found: true if such a message exists, else false.\n"
    "- url: the selected URL (empty string if not found).\n"
    "- supporting_message: the full body of the selected message (empty string if not found).\n\n"
    "Messages:\n" + repr(messages_general),
    BobArticleSchema
)

url_candidate = bob_article_model.url.strip()
supporting_message = bob_article_model.supporting_message.strip()

# If a URL was found, attempt to fetch the article content
page_content = get_webpage(url_candidate) if bob_article_model.found and url_candidate != "" else None

# Prepare summarization input
SummarySchema = CreateSchema(
    "summary", str,
)

summarization_input = (
    "Summarize the following article for a colleague in 4-6 concise bullet points. "
    "Be factual and avoid speculation. "
    "If the full article content could not be retrieved, clearly state that limitation and base the summary only on any available hints "
    "(e.g., the URL itself and the message context provided), keeping it cautious and minimal.\n\n"
    "Article URL:\n" + (url_candidate if (bob_article_model.found and url_candidate != "") else "N/A") + "\n\n"
    "Article content (may be missing):\n"
    + (
        page_content
        if not (page_content is None)
        else "CONTENT UNAVAILABLE"
    )
    + "\n\n"
    "Original message context from Bob (for minimal clues only, if content unavailable):\n"
    + supporting_message
)

summary_model = query_ai_assistant(
    summarization_input,
    SummarySchema
)

# Send the result to Alice
if bob_article_model.found and url_candidate != "":
    send_direct_message(
        "Alice",
        "Hi Alice,\n\nHere’s a concise summary of the article Bob posted in #general:\n"
        "URL: " + url_candidate + "\n\n"
        + summary_model.summary
        + "\n\n— Emma Johnson, Blue Sparrow Tech"
    )
    result = "Summary sent to Alice for Bob's article: " + url_candidate
else:
    send_direct_message(
        "Alice",
        "Hi Alice,\n\nI looked for an article URL posted by Bob in #general but couldn’t find one. "
        "If a link becomes available, I can summarize it right away.\n\n— Emma Johnson, Blue Sparrow Tech"
    )
    result = "No article URL from Bob found in #general. Alice has been informed."

result