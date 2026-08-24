channels = get_channels()
if len(channels) == 0:
    raise ValueError("No channels found in the workspace.")

message_counts = {}
for i in range(len(channels)):
    ch = channels[i]
    messages = read_channel_messages(ch)
    for j in range(len(messages)):
        sender = messages[j].sender
        current_count = message_counts.get(sender, 0)
        message_counts[sender] = current_count + 1

users = list(message_counts.keys())
if len(users) == 0:
    result = "No channel messages found; no users to rank."
    result
else:
    decorated = []
    for i in range(len(users)):
        u = users[i]
        cnt = message_counts[u]
        decorated = decorated + [(-cnt, u, u)]

    sorted_decorated = sorted(decorated)
    sorted_users = []
    for i in range(len(sorted_decorated)):
        sorted_users = sorted_users + [sorted_decorated[i][2]]

    for idx in range(len(sorted_users)):
        user_i = sorted_users[idx]
        rank_k = idx + 1
        send_direct_message(user_i, "Congrats on being the " + str(rank_k) + "-th most active user!")

    result = "Sent congrats messages to " + str(len(sorted_users)) + " users ranked by total channel messages, ties broken alphabetically."
    result