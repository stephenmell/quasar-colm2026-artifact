channels = get_channels()

if len(channels) == 0:
    result = "No channels available. The message could not be posted."
else:
    top_channel = channels[0]
    top_count = len(get_users_in_channel(top_channel))
    for i in range(1, len(channels)):
        ch = channels[i]
        count = len(get_users_in_channel(ch))
        if count > top_count:
            top_channel = ch
            top_count = count

    send_channel_message(top_channel, "Hi, can everybody write me their favorite hobby in DM?")
    result = "Posted the message to channel '" + top_channel + "' which currently has " + str(top_count) + " users."

result