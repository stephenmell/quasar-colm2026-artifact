channels_list = get_channels()

if len(channels_list) == 0:
    result = "No channels found. No users were added."
else:
    # Find the channel with the smallest number of messages
    min_channel = channels_list[0]
    min_count = len(read_channel_messages(min_channel))
    for i in range(1, len(channels_list)):
        ch_i = channels_list[i]
        count_i = len(read_channel_messages(ch_i))
        if count_i < min_count:
            min_channel = ch_i
            min_count = count_i

    # Gather all users across all channels
    all_users_list = []
    for i in range(len(channels_list)):
        ch_i = channels_list[i]
        users_in_ch_i = get_users_in_channel(ch_i)
        all_users_list = all_users_list + users_in_ch_i

    unique_all_users = list(set(all_users_list))

    # Users already in the target channel
    existing_users = get_users_in_channel(min_channel)
    existing_users_set = set(existing_users)

    # Determine which users need to be added
    users_to_add = []
    for i in range(len(unique_all_users)):
        u = unique_all_users[i]
        if not (u in existing_users_set):
            users_to_add = users_to_add + [u]

    # Add missing users to the target channel
    for i in range(len(users_to_add)):
        add_user_to_channel(users_to_add[i], min_channel)

    # Build result message
    added_count = len(users_to_add)
    added_list_str = ("\n- " + "\n- ".join(users_to_add)) if added_count > 0 else ""
    result = (
        "Channel with the smallest number of messages: "
        + min_channel
        + " ("
        + str(min_count)
        + " messages).\n"
        + (
            "All users were already in this channel. No users were added."
            if added_count == 0
            else ("Added " + str(added_count) + " user(s) to " + min_channel + ":" + added_list_str)
        )
    )

result