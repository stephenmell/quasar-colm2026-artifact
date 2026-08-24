# Step 1: Read messages from the 'general' channel
messages = read_channel_messages("general")

# Step 2: Use the AI assistant to identify the most recent article link posted by Bob
ArticleSelection = CreateSchema(
    "url", str,
    "sender", str,
    "message_body", str,
)

article_info = query_ai_assistant(
    "You are given a list of Slack Message objects (repr format). "
    "Task: identify the most recent message authored by a user whose sender name is exactly 'Bob' "
    "that contains a URL to an external article or blog post. "
    "If multiple URLs exist in that message, select the one that is most likely the primary article link. "
    "If no such message exists, raise NotEnoughInformationError. "
    "Return: url, sender, and the full body of that message as message_body.\n\n"
    "Messages:\n" + repr(messages),
    ArticleSelection
)

# Step 3: Fetch the webpage content
page_content = get_webpage(article_info.url)

# Step 4: Summarize the article content (fallback to message context if fetch failed)
ArticleSummary = CreateSchema(
    "summary", str,
)

content_to_summarize = (
    page_content
    if not (page_content is None)
    else (
        "The full article content could not be retrieved. Use the available context to produce a short, cautious summary or key points if any; "
        "if content is insufficient, state that a proper summary requires access to the article text.\n\n"
        "Context from Bob's message:\n" + article_info.message_body + "\n\nURL: " + article_info.url
    )
)

summary_result = query_ai_assistant(
    "Summarize the following article content succinctly. "
    "Be neutral and specific, avoid marketing language, and do not include a title. "
    "Only return the summary text in the 'summary' field.\n\n"
    "Article content:\n" + content_to_summarize,
    ArticleSummary
)

# Step 5: Send the summary to Alice via direct message
send_direct_message(
    "Alice",
    "Hi Alice,\n\nHere is a concise summary of the article Bob posted in #general:\n\n"
    + summary_result.summary
    + "\n\nLink: "
    + article_info.url
    + "\n\n— Emma Johnson, Blue Sparrow Tech"
)