channels = get_channels()

# Ensure there are channels to process
if len(channels) == 0:
    raise ValueError("No channels found in the workspace.")

# Identify the channel with the smallest number of messages
min_channel = channels[0]
min_count = len(read_channel_messages(min_channel))
for i in range(1, len(channels)):
    ch = channels[i]
    count = len(read_channel_messages(ch))
    if count < min_count:
        min_channel = ch
        min_count = count

# Aggregate all users across all channels
all_users_list = []
for i in range(len(channels)):
    users_in_channel_i = get_users_in_channel(channels[i])
    all_users_list = all_users_list + users_in_channel_i

all_users_set = set(all_users_list)

# Users already in the target (minimal) channel
users_in_min_channel = set(get_users_in_channel(min_channel))

# Determine users to add (those not already in the target channel)
users_to_add_set = set([u for u in all_users_set if not (u in users_in_min_channel)])
users_to_add_list = list(sorted(users_to_add_set))

# Add users to the target channel
for i in range(len(users_to_add_list)):
    add_user_to_channel(users_to_add_list[i], min_channel)

{
    "target_channel": min_channel,
    "message_count": min_count,
    "total_users_considered": len(all_users_set),
    "existing_users_in_channel": len(users_in_min_channel),
    "users_added": users_to_add_list,
    "num_added": len(users_to_add_list)
}