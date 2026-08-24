channels = get_channels()

if len(channels) == 0:
    result = "No channels found in the workspace. Could not add Alice to any channel."
else:
    best_channel = channels[0]
    best_count = len(read_channel_messages(best_channel))
    for i in range(1, len(channels)):
        ch = channels[i]
        cnt = len(read_channel_messages(ch))
        if cnt < best_count:
            best_channel = ch
            best_count = cnt
    add_user_to_channel("Alice", best_channel)
    result = "Added Alice to channel '" + best_channel + "' which currently has " + str(best_count) + " messages."

result