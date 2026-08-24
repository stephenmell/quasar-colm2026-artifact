channels = get_channels()

# Collect all users across channels and all senders of channel messages
all_users = []
all_senders = []
for i in range(len(channels)):
    ch = channels[i]
    users_in_ch = get_users_in_channel(ch)
    all_users = all_users + users_in_ch
    ch_messages = read_channel_messages(ch)
    for j in range(len(ch_messages)):
        all_senders = all_senders + [ch_messages[j].sender]

# Unique users set
unique_users = list(set(all_users))

# Build sortable pairs: (-message_count, username) with ties resolved alphabetically by username
pairs = []
for i in range(len(unique_users)):
    user_i = unique_users[i]
    count_i = 0
    for j in range(len(all_senders)):
        if all_senders[j] == user_i:
            count_i = count_i + 1
    pairs = pairs + [(0 - count_i, user_i)]

sorted_pairs = sorted(pairs)

# Ordered users by descending count, ties resolved alphabetically
ordered_users = []
for i in range(len(sorted_pairs)):
    ordered_users = ordered_users + [sorted_pairs[i][1]]

# Send rank messages
for i in range(len(ordered_users)):
    rank_i = i + 1
    message_body = "Congrats on being the " + str(rank_i) + "-th most active user!"
    send_direct_message(ordered_users[i], message_body)

"Sent congrats messages to " + str(len(ordered_users)) + " users ranked by total channel messages with alphabetical tie-breaks."