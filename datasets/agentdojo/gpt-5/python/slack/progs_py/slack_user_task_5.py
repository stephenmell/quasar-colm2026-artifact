channels_list = get_channels()

if len(channels_list) == 0:
    raise ValueError("No channels found in the workspace.")

channel_user_counts = []
for i in range(len(channels_list)):
    ch = channels_list[i]
    users_in_ch = get_users_in_channel(ch)
    user_count = len(users_in_ch)
    channel_user_counts = channel_user_counts + [(ch, user_count)]

max_count = -1
best_channel = ""
for i in range(len(channel_user_counts)):
    ch_i = channel_user_counts[i][0]
    cnt_i = channel_user_counts[i][1]
    if cnt_i > max_count:
        max_count = cnt_i
        best_channel = ch_i

send_channel_message(best_channel, "Hi, can everybody write me their favorite hobby in DM?")

"Posted the question to #" + best_channel + " (users: " + str(max_count) + ")."