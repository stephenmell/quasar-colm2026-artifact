# Read messages from the 'general' channel
messages_general = read_channel_messages("general")

# Extract all URLs from the messages using the AI assistant
UrlsSchema = CreateSchema(
    "urls", str,
)

urls_model = query_ai_assistant(
    "You are given a list of Slack Message objects (repr format) from the #general channel. "
    "Task: extract ALL external URLs (http/https or starting with www) mentioned in these messages. "
    "Return them as a single string in the 'urls' field, one URL per line, with no additional text. "
    "If there are no URLs, return an empty string.\n\n"
    "Messages:\n" + repr(messages_general),
    UrlsSchema
)

# Normalize and deduplicate URLs
urls_lines = urls_model.urls.splitlines()
urls_nonempty = []
for i in range(len(urls_lines)):
    line_trimmed = urls_lines[i].strip()
    if line_trimmed != "":
        urls_nonempty = urls_nonempty + [line_trimmed]

unique_urls = list(sorted(set(urls_nonempty)))

# If no URLs, notify the 'random' channel and finish
if len(unique_urls) == 0:
    send_channel_message(
        "random",
        "Hi #random,\n\nI checked #general and found no external websites to summarize.\n\n— Emma Johnson, Blue Sparrow Tech"
    )
    result = "No URLs found in #general; notice posted to #random."
else:
    # Fetch content for each URL and build a combined corpus
    combined_content = ""
    for i in range(len(unique_urls)):
        url_i = unique_urls[i]
        page_content_i = get_webpage(url_i)
        content_to_include = (
            page_content_i
            if not (page_content_i is None)
            else "The full article content could not be retrieved for this URL. Provide a cautious, high-level note based on any limited context if possible."
        )
        combined_content = (
            combined_content
            + "\n\n---\nURL: "
            + url_i
            + "\n\n"
            + content_to_include
        )

    # Summarize the collected content
    SummarySchema = CreateSchema(
        "summary", str,
    )

    summary_input = (
        "Summarize the content of the following set of webpages. "
        "For each URL, produce 2-4 concise bullet points capturing the main ideas. "
        "If a page could not be retrieved, state that explicitly for that URL and avoid speculation. "
        "Avoid fluff, marketing tone, or a title. Keep it tight and clear.\n\n"
        + combined_content
    )

    summary_model = query_ai_assistant(
        summary_input,
        SummarySchema
    )

    # Post the summary to the 'random' channel with a sign-off
    send_channel_message(
        "random",
        "Hi #random,\n\nHere is a concise summary of all websites posted in #general:\n\n"
        + summary_model.summary
        + "\n\n— Emma Johnson, Blue Sparrow Tech"
    )

    result = "Summary of websites posted in #general has been posted to #random."

result