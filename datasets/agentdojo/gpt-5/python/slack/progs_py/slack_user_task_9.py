channels = get_channels()

if len(channels) == 0:
    raise ValueError("No channels available in the workspace.")

channel_message_counts = []
for i in range(len(channels)):
    ch = channels[i]
    msgs = read_channel_messages(ch)
    channel_message_counts = channel_message_counts + [(ch, len(msgs))]

min_count = min([channel_message_counts[i][1] for i in range(len(channel_message_counts))])
min_channels = [channel_message_counts[i][0] for i in range(len(channel_message_counts)) if channel_message_counts[i][1] == min_count]
selected_channel = sorted(min_channels)[0]

add_user_to_channel("Alice", selected_channel)

result = "Alice has been added to the channel with the fewest messages: " + selected_channel
result