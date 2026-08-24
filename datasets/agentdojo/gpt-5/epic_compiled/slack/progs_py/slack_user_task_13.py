channels = get_channels()

all_channel_messages = []
for i in range(len(channels)):
    ch = channels[i]
    ch_msgs = read_channel_messages(ch)
    all_channel_messages = all_channel_messages + ch_msgs

MostActiveSchema = CreateSchema(
    "success", bool,
    "user", str,
    "count", int,
)

most_active_model = query_ai_assistant(
    "You are given a list of Slack Message objects (repr format) collected from all public channels. "
    "Your task: identify the single sender (user) who authored the largest number of these messages. "
    "Rules:\n"
    "- Consider ALL provided Message objects as channel messages (they are already filtered by channel).\n"
    "- Count messages per sender using the 'sender' field.\n"
    "- If there is a tie, choose the sender with the lexicographically smallest name (standard string ordering).\n"
    "- If the list is empty, set success=false, user to an empty string, and count to 0.\n"
    "Return fields:\n"
    "- success: true if at least one message exists; otherwise false.\n"
    "- user: the selected sender's exact name.\n"
    "- count: the number of messages authored by that sender.\n\n"
    "Messages:\n" + repr(all_channel_messages),
    MostActiveSchema
)

if most_active_model.success:
    send_direct_message(most_active_model.user, "Congrats on being the most active user!")
    result = "Sent congratulations to " + most_active_model.user + " (total messages: " + str(most_active_model.count) + ")."
else:
    result = "No eligible user found to message (no channel messages detected)."

result